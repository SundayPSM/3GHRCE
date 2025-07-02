"""
CMS API Client

Handles all interactions with CMS Data APIs including UUID extraction,
data fetching, and CSV downloads for the CMS Data Processing Tool.
"""

import logging
import re
import httpx
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from io import StringIO
import pandas as pd
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class CMSAPIClient:
    """Client for interacting with CMS Data APIs."""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.base_url = "https://data.cms.gov"
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (CMS Data Processing Tool)'
        }
    
    def extract_slug_from_url(self, url: str) -> str:
        """
        Extracts a dataset slug from the API documentation URL.

        Args:
            url (str): The URL string of the API documentation.

        Returns:
            str: Dataset slug derived from the URL.
        """
        path = urlparse(url).path
        slug = path.strip("/").split("/")[-2]
        return slug.replace("-", "_")
    
    async def get_dataset_uuid(self, api_docs_url: str) -> Optional[str]:
        """
        Uses Playwright to open an API documentation page and extract the dataset UUID.

        Args:
            api_docs_url (str): URL of the API documentation.

        Returns:
            Optional[str]: UUID of the dataset if found, otherwise None.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            requests = []
            page.on("request", lambda request: requests.append(request.url))
            
            logger.info(f"Opening: {api_docs_url}")
            await page.goto(api_docs_url, wait_until="networkidle")
            await page.wait_for_timeout(5000)
            await browser.close()
            
            for url in requests:
                match = re.search(r'/dataset/([a-z0-9-]{36})', url)
                logger.info(f"URL: {url}")
                logger.info(f"Match: {match}")
                if match:
                    dataset_uuid = match.group(1)
                    logger.info(f"Dataset UUID found: {dataset_uuid}")
                    return dataset_uuid
            
            logger.error("Dataset UUID not found.")
            return None
    
    async def fetch_all_data(self, dataset_uuid: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches all data for a dataset using its UUID via CMS Data API without pagination.

        Args:
            dataset_uuid (str): UUID of the dataset.

        Returns:
            Optional[List[Dict[str, Any]]]: List of records if data is fetched successfully, otherwise None.
        """
        url = f"{self.base_url}/data-api/v1/dataset/{dataset_uuid}/data"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Fetching all data for dataset {dataset_uuid}...")
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    # Handle different response structures
                    if isinstance(data, list):
                        records = data
                    elif isinstance(data, dict) and "data" in data:
                        records = data["data"]
                    else:
                        logger.error(f"Unexpected response structure for dataset {dataset_uuid}")
                        return None
                    
                    logger.info(f"Fetched {len(records)} records from dataset {dataset_uuid}")
                    return records
                else:
                    logger.error(f"Failed to fetch data: {response.status_code}")
                    return None
            except Exception as e:
                logger.error(f"Exception while fetching data: {str(e)}")
                return None
    
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
    
    async def fetch_and_insert_data(self, dataset_uuid: str, table_name: str, 
                                  datayear: str, db_manager, update_checker) -> bool:
        """
        Fetches data from CMS API and directly inserts it into the database.
        Also updates the CheckDBUpdate table.

        Args:
            dataset_uuid (str): UUID of the dataset.
            table_name (str): Name of the table to insert data into.
            datayear (str): Year/month of the data.
            db_manager: MySQL database manager instance.
            update_checker: Update checker instance.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Fetch all data from API
            logger.info(f"Fetching data for {table_name} with UUID {dataset_uuid}")
            data = await self.fetch_all_data(dataset_uuid)
            
            if not data:
                logger.error(f"No data received for {table_name}")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            logger.info(f"Converted {len(df)} records to DataFrame for {table_name}")
            
            # Debug: Print column names for nh_performance_measures
            if table_name == "nh_performance_measures":
                logger.info(f"nh_performance_measures API columns: {list(df.columns)}")
            
            # Clean the DataFrame and ensure all data is string
            df_clean = self._clean_dataframe(df)
            
            # Add datayear column for relevant tables
            if table_name in ["snf_owners", "snf_enrollments", "snf_ownership_changes", "nh_performance_measures"]:
                df_clean["datayear"] = datayear

            # Get predefined schema for this table
            schema_columns = Settings.TABLE_SCHEMAS.get(table_name, [])
            
            if not schema_columns:
                logger.error(f"No predefined schema found for table {table_name}")
                return False
            
            # Align DataFrame columns with predefined schema
            df_aligned = self._align_dataframe_to_schema(df_clean, schema_columns, table_name)
            
            # Create table using predefined schema
            if db_manager.create_table_with_schema(table_name, schema_columns):
                if db_manager.insert_data(table_name, df_aligned):
                    # Update CheckDBUpdate table
                    if update_checker.update_processed_data(table_name, datayear, dataset_uuid):
                        logger.info(f"Successfully processed {table_name}: {datayear} - {dataset_uuid}")
                        return True
                    else:
                        logger.error(f"Failed to update CheckDBUpdate for {table_name}")
                        return False
                else:
                    logger.error(f"Failed to insert data into {table_name}")
                    return False
            else:
                logger.error(f"Failed to create table {table_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error in fetch_and_insert_data for {table_name}: {e}")
            return False

    def _align_dataframe_to_schema(self, df: pd.DataFrame, schema_columns: list, table_name: str = None) -> pd.DataFrame:
        """
        Aligns DataFrame columns with predefined schema, filling missing columns with empty strings.
        Uses column mapping if available for the table.
        
        Args:
            df (pd.DataFrame): Original DataFrame
            schema_columns (list): List of expected column names
            table_name (str): Name of the table for column mapping
            
        Returns:
            pd.DataFrame: DataFrame aligned with schema
        """
        try:
            # Get column mapping for this table if available
            column_mapping = Settings.COLUMN_MAPPINGS.get(table_name, {})
            
            # Create a new DataFrame with the exact schema columns
            df_aligned = pd.DataFrame(columns=schema_columns)
            
            # For each row in the original DataFrame, map values to schema columns
            aligned_rows = []
            for _, row in df.iterrows():
                new_row = {}
                for col in schema_columns:
                    # Try to find the value using column mapping first
                    value_found = False
                    for api_col, db_col in column_mapping.items():
                        if db_col == col and api_col in row:
                            new_row[col] = str(row[api_col]) if pd.notna(row[api_col]) else ""
                            value_found = True
                            break
                    
                    # If not found via mapping, try direct match
                    if not value_found:
                        if col in row:
                            new_row[col] = str(row[col]) if pd.notna(row[col]) else ""
                        else:
                            new_row[col] = ""
                aligned_rows.append(new_row)
            
            # Create new DataFrame with aligned data
            df_aligned = pd.DataFrame(aligned_rows, columns=schema_columns)
            
            # Ensure all data is string type
            for col in df_aligned.columns:
                df_aligned[col] = df_aligned[col].astype(str)
            
            logger.info(f"Aligned DataFrame from {len(df.columns)} to {len(schema_columns)} columns")
            return df_aligned
            
        except Exception as e:
            logger.error(f"Error aligning DataFrame to schema: {e}")
            return df
    
    async def get_csv_metadata(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches metadata for a CSV dataset.

        Args:
            dataset_id (str): ID of the dataset.

        Returns:
            Optional[Dict[str, Any]]: Metadata if found, otherwise None.
        """
        metadata_url = f"{self.base_url}/provider-data/api/1/metastore/schemas/dataset/items/{dataset_id}?show-reference-ids=false"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Fetching metadata for dataset {dataset_id}")
                response = await client.get(metadata_url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to retrieve metadata: {e}")
                return None
    
    async def download_csv_data(self, download_url: str) -> Optional[pd.DataFrame]:
        """
        Downloads and parses CSV data from a URL.

        Args:
            download_url (str): URL to download CSV from.

        Returns:
            Optional[pd.DataFrame]: DataFrame if successful, otherwise None.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info("Downloading CSV file...")
                csv_response = await client.get(download_url)
                csv_response.raise_for_status()
                csv_data = csv_response.text
                df = pd.read_csv(StringIO(csv_data))
                logger.info(f"CSV loaded with shape: {df.shape}")
                return df
            except Exception as e:
                logger.error(f"Failed to download or parse CSV: {e}")
                return None
    
    def extract_download_url(self, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Extracts download URL from dataset metadata.

        Args:
            metadata (Dict[str, Any]): Dataset metadata.

        Returns:
            Optional[str]: Download URL if found, otherwise None.
        """
        try:
            distributions = metadata.get("distribution", [])
            if not distributions:
                logger.error("No distributions found in metadata")
                return None

            download_url = distributions[0]["data"]["downloadURL"]
            logger.info(f"CSV download URL: {download_url}")
            return download_url
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting download URL: {e}")
            return None 