"""
Dataset Orchestrator

Coordinates the complete flow:
1. Scrape Dataset Versions from all API docs
2. Check CheckDBUpdate table for existing data
3. Fetch API data for needed UUIDs
4. Insert data into respective MySQL tables
5. Update CheckDBUpdate table
"""

import logging
import asyncio
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from tqdm import tqdm
import re
from datetime import datetime

from ..html_scrapers.dataset_versions_scraper import DatasetVersionsScraper
from ..data_extraction.cms_api_client import CMSAPIClient
from ..database.mysql_manager import MySQLManager
from ..database.update_checker import UpdateChecker
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class DatasetOrchestrator:
    """Orchestrates the complete dataset processing pipeline."""
    
    def __init__(self):
        self.scraper = DatasetVersionsScraper(timeout=Settings.API_CONFIG['timeout'])
        self.api_client = CMSAPIClient()
        self.db_manager = MySQLManager(
            host=Settings.DB_CONFIG['host'],
            port=Settings.DB_CONFIG['port'],
            user=Settings.DB_CONFIG['user'],
            password=Settings.DB_CONFIG['password'],
            database=Settings.DB_CONFIG['database']
        )
        self.update_checker = UpdateChecker(self.db_manager)
        # Use centralized mapping from settings
        self.url_to_table_map = Settings.URL_TO_TABLE_MAP
    
    def _parse_datayear(self, datayear: str) -> datetime:
        """
        Parse datayear string into a datetime object for sorting.
        Handles formats like:
        - "January 2025", "February 2025", etc.
        - "Q1 2025", "Q2 2025", etc.
        - "2025", "2024", etc.
        
        Args:
            datayear (str): The datayear string to parse
            
        Returns:
            datetime: Parsed datetime object
        """
        datayear = datayear.strip()
        
        # Handle month formats: "January 2025", "Feb 2025", etc.
        month_pattern = r'(\w+)\s+(\d{4})'
        month_match = re.match(month_pattern, datayear, re.IGNORECASE)
        if month_match:
            month_str, year_str = month_match.groups()
            month_map = {
                'january': 1, 'jan': 1,
                'february': 2, 'feb': 2,
                'march': 3, 'mar': 3,
                'april': 4, 'apr': 4,
                'may': 5,
                'june': 6, 'jun': 6,
                'july': 7, 'jul': 7,
                'august': 8, 'aug': 8,
                'september': 9, 'sep': 9, 'sept': 9,
                'october': 10, 'oct': 10,
                'november': 11, 'nov': 11,
                'december': 12, 'dec': 12
            }
            month = month_map.get(month_str.lower())
            if month:
                return datetime(int(year_str), month, 1)
        
        # Handle quarter formats: "Q1 2025", "Q2 2025", etc.
        quarter_pattern = r'Q(\d)\s+(\d{4})'
        quarter_match = re.match(quarter_pattern, datayear, re.IGNORECASE)
        if quarter_match:
            quarter, year_str = quarter_match.groups()
            quarter = int(quarter)
            # Convert quarter to month (Q1=Jan, Q2=Apr, Q3=Jul, Q4=Oct)
            month = (quarter - 1) * 3 + 1
            return datetime(int(year_str), month, 1)
        
        # Handle year-only formats: "2025", "2024", etc.
        year_pattern = r'(\d{4})'
        year_match = re.match(year_pattern, datayear)
        if year_match:
            year = int(year_match.group(1))
            return datetime(year, 1, 1)
        
        # If we can't parse it, return a very old date so it sorts to the beginning
        logger.warning(f"Could not parse datayear format: {datayear}")
        return datetime(1900, 1, 1)
    
    def _sort_versions_chronologically(self, version_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        Sort dataset versions chronologically (oldest to newest).
        
        Args:
            version_list (List[Tuple[str, str]]): List of (datayear, uuid) pairs
            
        Returns:
            List[Tuple[str, str]]: Sorted list of (datayear, uuid) pairs
        """
        try:
            # Sort by parsed datetime
            sorted_versions = sorted(version_list, key=lambda x: self._parse_datayear(x[0]))
            logger.info(f"Sorted {len(sorted_versions)} versions chronologically")
            return sorted_versions
        except Exception as e:
            logger.error(f"Error sorting versions: {e}")
            return version_list
    
    async def run_complete_pipeline(self) -> bool:
        """
        Runs the complete dataset processing pipeline.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info("Starting complete dataset processing pipeline")
            
            # Step 1: Ensure CheckDBUpdate table exists
            if not self.update_checker.create_check_table():
                logger.error("Failed to create CheckDBUpdate table")
                return False
            
            # Step 2: Scrape Dataset Versions from all API docs
            scraped_data = await self._scrape_all_dataset_versions()
            logger.info(f"Scraped data: {scraped_data}")
            if not scraped_data:
                logger.error("Failed to scrape dataset versions")
                return False
            
            # Step 3: Determine which datasets need updating
            update_needs = self.update_checker.determine_update_needs(scraped_data)
            
            if not update_needs:
                logger.info("No datasets need updating - all data is current")
                return True
            
            # Step 4: Process each dataset that needs updating
            success_count = 0
            for table_name, uuids_to_fetch in update_needs.items():
                logger.info(f"Processing {table_name} - fetching {len(uuids_to_fetch)} versions")
                
                if await self._process_dataset(table_name, uuids_to_fetch, scraped_data[table_name]):
                    success_count += 1
                else:
                    logger.error(f"Failed to process {table_name}")
            
            # Step 5: Cleanup orphaned records
            self.update_checker.cleanup_orphaned_records(list(scraped_data.keys()))
            
            logger.info(f"Pipeline completed: {success_count}/{len(update_needs)} datasets processed successfully")
            return success_count == len(update_needs)
            
        except Exception as e:
            logger.error(f"Error in complete pipeline: {e}")
            return False
    
    async def _scrape_all_dataset_versions(self) -> Optional[Dict[str, List[Tuple[str, str]]]]:
        """
        Scrapes Dataset Versions from all API docs.
        
        Returns:
            Optional[Dict[str, List[Tuple[str, str]]]]: Dict[table_name, List[Tuple[datayear, uuid]]]
        """
        scraped_data = {}
        
        for url in Settings.API_DOCS_URLS:
            try:
                table_name = self.url_to_table_map.get(url)
                if not table_name:
                    logger.warning(f"No table mapping found for URL: {url}")
                    continue
                
                logger.info(f"Scraping Dataset Versions for {table_name}")
                
                # Scrape the Dataset Versions table
                df = await self.scraper.scrape(url)
                if df is None or df.empty:
                    logger.warning(f"No data scraped for {table_name}")
                    continue
                
                # Get last 6 months (first 6 rows)
                df_last_6 = df.head(6)
                
                # Convert to list of tuples (datayear, uuid)
                version_list = []
                for _, row in df_last_6.iterrows():
                    version_list.append((row['Version'], row['UUID']))
                
                # Sort versions chronologically (oldest to newest)
                version_list = self._sort_versions_chronologically(version_list)
                
                scraped_data[table_name] = version_list
                logger.info(f"Scraped {len(version_list)} versions for {table_name}")
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue
        
        return scraped_data if scraped_data else None
    
    async def _process_dataset(self, table_name: str, uuids_to_fetch: List[str], 
                             version_list: List[Tuple[str, str]]) -> bool:
        """
        Processes a single dataset: fetches data and inserts into database.
        
        Args:
            table_name (str): Name of the table to insert data into.
            uuids_to_fetch (List[str]): List of UUIDs to fetch data for.
            version_list (List[Tuple[str, str]]): List of (datayear, uuid) pairs.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            logger.info(f"Processing dataset {table_name} with {len(uuids_to_fetch)} UUIDs")
            # Ensure DB connection before processing
            if not self.db_manager.get_connection():
                logger.error("No database connection available. Skipping dataset processing.")
                return False
            # Process each UUID individually to ensure proper tracking
            success_count = 0
            for idx, uuid in enumerate(tqdm(uuids_to_fetch, desc=f"{table_name} Progress")):
                # Find the corresponding datayear for this UUID
                datayear = None
                for dy, uid in version_list:
                    if uid == uuid:
                        datayear = dy
                        break
                print(f"Processing Table: {table_name}, DataYear: {datayear}, UUID: {uuid} ({idx+1}/{len(uuids_to_fetch)})")
                logger.info(f"Processing UUID: {uuid}")
                if not datayear:
                    logger.warning(f"Could not find datayear for UUID {uuid}")
                    continue
                # Use the new method that handles everything in one go
                if await self.api_client.fetch_and_insert_data(uuid, table_name, datayear, 
                                                              self.db_manager, self.update_checker):
                    success_count += 1
                    logger.info(f"Successfully processed UUID {uuid} for {table_name}")
                else:
                    logger.error(f"Failed to process UUID {uuid} for {table_name}")
            logger.info(f"Processed {success_count}/{len(uuids_to_fetch)} UUIDs for {table_name}")
            return success_count > 0
        except Exception as e:
            logger.error(f"Error processing dataset {table_name}: {e}")
            return False
    
    async def get_processing_summary(self) -> Dict[str, Any]:
        """
        Gets a summary of the current processing state.
        
        Returns:
            Dict[str, Any]: Summary information.
        """
        try:
            # Get all tracked tables
            tracked_tables = self.update_checker.get_all_tracked_tables()
            
            # Get last processed data for each table
            summary = {}
            for table_name in tracked_tables:
                last_data = self.update_checker.get_last_processed_data(table_name)
                if last_data:
                    datayear, uuid = last_data
                    summary[table_name] = {
                        "last_processed_date": datayear,
                        "last_processed_uuid": uuid
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting processing summary: {e}")
            return {}


async def main():
    """Test function for the orchestrator."""
    orchestrator = DatasetOrchestrator()
    
    print("Starting Dataset Processing Pipeline")
    print("-" * 50)
    
    # Run the complete pipeline
    success = await orchestrator.run_complete_pipeline()
    
    if success:
        print("✅ Pipeline completed successfully!")
    else:
        print("❌ Pipeline completed with errors")
    
    # Get summary
    summary = await orchestrator.get_processing_summary()
    print("\n📊 Processing Summary:")
    for table_name, info in summary.items():
        print(f"  {table_name}: {info['last_processed_date']} - {info['last_processed_uuid']}")


if __name__ == "__main__":
    asyncio.run(main()) 