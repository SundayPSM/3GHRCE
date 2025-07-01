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

from ..html_scrapers.dataset_versions_scraper import DatasetVersionsScraper
from ..data_extraction.cms_api_client import CMSAPIClient
from ..database.mysql_manager import MySQLManager
from ..database.update_checker import UpdateChecker
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class DatasetOrchestrator:
    """Orchestrates the complete dataset processing pipeline."""
    
    def __init__(self):
        self.scraper = DatasetVersionsScraper()
        self.api_client = CMSAPIClient()
        self.db_manager = MySQLManager()
        self.update_checker = UpdateChecker(self.db_manager)
        
        # Map API docs URLs to table names
        self.url_to_table_map = {
            "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-all-owners/api-docs": "snf_owners",
            "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-enrollments/api-docs": "snf_enrollments",
            "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-change-of-ownership/api-docs": "snf_ownership_changes",
            "https://data.cms.gov/quality-of-care/nursing-home-affiliated-entity-performance-measures/api-docs": "nh_performance_measures"
        }
    
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
            
            # Process each UUID individually to ensure proper tracking
            success_count = 0
            for uuid in uuids_to_fetch:
                logger.info(f"Processing UUID: {uuid}")
                
                # Find the corresponding datayear for this UUID
                datayear = None
                for dy, uid in version_list:
                    if uid == uuid:
                        datayear = dy
                        break
                
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