"""
Dataset Processor

Orchestrates the processing of CMS datasets including data extraction,
transformation, and storage for the CMS Data Processing Tool.
"""

import logging
import os
import pandas as pd
from typing import Optional, List, Dict, Any

from ..data_extraction.cms_api_client import CMSAPIClient
from ..database.mysql_manager import MySQLManager

logger = logging.getLogger(__name__)


class DatasetProcessor:
    """Processes CMS datasets and stores them in CSV and MySQL."""
    
    def __init__(self, csv_folder: str = "csv", db_manager: Optional[MySQLManager] = None):
        self.csv_folder = csv_folder
        self.api_client = CMSAPIClient()
        self.db_manager = db_manager or MySQLManager()
        
        # Map dataset slugs to table names
        self.slug_to_table_map = {
            "skilled_nursing_facility_all_owners": "snf_owners",
            "skilled_nursing_facility_enrollments": "snf_enrollments", 
            "skilled_nursing_facility_change_of_ownership": "snf_ownership_changes",
            "nursing_home_affiliated_entity_performance_measures": "nh_performance_measures",
            "change_of_ownership": "snf_ownership_changes"
        }
        
        # Create CSV folder if it doesn't exist
        if not os.path.exists(csv_folder):
            os.makedirs(csv_folder)
            logger.info(f"Created directory: {csv_folder}")
    
    def _get_table_name(self, dataset_slug: str) -> str:
        """
        Maps dataset slug to table name.
        
        Args:
            dataset_slug (str): Original dataset slug.
            
        Returns:
            str: Mapped table name.
        """
        return self.slug_to_table_map.get(dataset_slug, dataset_slug)
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the DataFrame by converting all data to strings and handling special cases.
        
        Args:
            df (pd.DataFrame): Raw DataFrame from API response.
            
        Returns:
            pd.DataFrame: Cleaned DataFrame with all data as strings.
        """
        try:
            logger.info(f"Cleaning DataFrame with shape: {df.shape}")
            
            # Create a copy to avoid modifying the original
            df_clean = df.copy()
            
            # Convert all columns to string type
            for col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str)
            
            # Replace 'nan' strings with empty strings
            df_clean = df_clean.replace('nan', '')
            df_clean = df_clean.replace('None', '')
            
            # Handle any remaining NaN values
            df_clean = df_clean.fillna('')
            
            # Trim whitespace from string columns
            for col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].str.strip()
            
            logger.info(f"DataFrame cleaned successfully. Final shape: {df_clean.shape}")
            return df_clean
            
        except Exception as e:
            logger.error(f"Error cleaning DataFrame: {e}")
            # Return original DataFrame if cleaning fails
            return df
    
    async def process_api_dataset(self, api_docs_url: str) -> bool:
        """
        Processes an API-based CMS dataset.

        Args:
            api_docs_url (str): URL of the API documentation for the dataset.

        Returns:
            bool: True if processing successful, False otherwise.
        """
        try:
            # Extract dataset slug
            dataset_slug = self.api_client.extract_slug_from_url(api_docs_url)
            if "change-of-ownership" in api_docs_url:
                dataset_slug = "change_of_ownership"
            
            logger.info(f"Processing API dataset: {dataset_slug}")
            
            # Get dataset UUID
            dataset_uuid = await self.api_client.get_dataset_uuid(api_docs_url)
            if not dataset_uuid:
                logger.error(f"Could not get UUID for {dataset_slug}")
                return False
            
            # Fetch data
            data = await self.api_client.fetch_all_data(dataset_uuid)
            if not data:
                logger.error(f"No data found for {dataset_slug}")
                return False
            
            # Process and store data
            return await self._process_and_store_data(dataset_slug, data)
            
        except Exception as e:
            logger.error(f"Error processing API dataset {api_docs_url}: {e}")
            return False
    
    async def process_csv_dataset(self, dataset_id: str, dataset_slug: Optional[str] = None) -> bool:
        """
        Processes a CMS dataset available as direct CSV download.

        Args:
            dataset_id (str): ID of the dataset.
            dataset_slug (Optional[str]): Optional slug to name the output files and tables.

        Returns:
            bool: True if processing successful, False otherwise.
        """
        try:
            if not dataset_slug:
                dataset_slug = "provider"
            
            logger.info(f"Processing CSV dataset: {dataset_slug} (ID: {dataset_id})")
            
            # Get metadata
            metadata = await self.api_client.get_csv_metadata(dataset_id)
            if not metadata:
                logger.error(f"Could not get metadata for {dataset_slug}")
                return False
            
            # Extract download URL
            download_url = self.api_client.extract_download_url(metadata)
            if not download_url:
                logger.error(f"Could not get download URL for {dataset_slug}")
                return False
            
            # Download and process data
            df = await self.api_client.download_csv_data(download_url)
            if df is None:
                logger.error(f"Could not download data for {dataset_slug}")
                return False
            
            # Process and store data
            return await self._process_and_store_dataframe(dataset_slug, df)
            
        except Exception as e:
            logger.error(f"Error processing CSV dataset {dataset_id}: {e}")
            return False
    
    async def process_state_average_dataset(self) -> bool:
        """
        Processes the state average performance dataset.

        Returns:
            bool: True if processing successful, False otherwise.
        """
        try:
            dataset_slug = "state_average"
            dataset_id = "xcdc-v8bm"
            
            logger.info(f"Processing state average dataset: {dataset_slug}")
            
            # Get metadata
            metadata = await self.api_client.get_csv_metadata(dataset_id)
            if not metadata:
                logger.error(f"Could not get metadata for {dataset_slug}")
                return False
            
            # Extract download URL
            download_url = None
            if 'distribution' in metadata:
                distributions = metadata['distribution']
                if distributions and len(distributions) > 0:
                    download_url = distributions[0].get('data', {}).get('downloadURL')
            
            if not download_url:
                logger.error("Could not find download URL in metadata")
                return False
            
            # Download and process data
            df = await self.api_client.download_csv_data(download_url)
            if df is None:
                logger.error(f"Could not download data for {dataset_slug}")
                return False
            
            # Process and store data
            return await self._process_and_store_dataframe(dataset_slug, df)
            
        except Exception as e:
            logger.error(f"Error processing state average dataset: {e}")
            return False
    
    async def _process_and_store_data(self, dataset_slug: str, data: List[Dict[str, Any]]) -> bool:
        """
        Processes raw data and stores it in CSV and MySQL.

        Args:
            dataset_slug (str): Name of the dataset.
            data (List[Dict[str, Any]]): Raw data to process.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Process and store
            return await self._process_and_store_dataframe(dataset_slug, df)
            
        except Exception as e:
            logger.error(f"Error processing data for {dataset_slug}: {e}")
            return False
    
    async def _process_and_store_dataframe(self, dataset_slug: str, df: pd.DataFrame) -> bool:
        """
        Processes DataFrame and stores it in CSV and MySQL.

        Args:
            dataset_slug (str): Name of the dataset.
            df (pd.DataFrame): DataFrame to process.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Clean the DataFrame
            df_clean = self._clean_dataframe(df)
            
            # Get the mapped table name
            table_name = self._get_table_name(dataset_slug)
            
            # Preview data
            print(f"\nPreview of {dataset_slug} data (table: {table_name}):")
            print(df_clean.head())
            
            # Save to CSV
            csv_filename = os.path.join(self.csv_folder, f"{dataset_slug}.csv")
            df_clean.to_csv(csv_filename, index=False)
            logger.info(f"Data saved to CSV: {csv_filename}")
            
            # Store in MySQL
            if self.db_manager:
                conn = self.db_manager.get_connection()
                if conn:
                    try:
                        success = self.db_manager.create_table(table_name, df_clean)
                        if success:
                            success = self.db_manager.insert_data(table_name, df_clean)
                            if success:
                                logger.info(f"Successfully processed {dataset_slug} -> {table_name}")
                                return True
                    finally:
                        self.db_manager.close_connection()
            
            logger.error(f"Failed to store {dataset_slug} in database")
            return False
            
        except Exception as e:
            logger.error(f"Error processing DataFrame for {dataset_slug}: {e}")
            return False 