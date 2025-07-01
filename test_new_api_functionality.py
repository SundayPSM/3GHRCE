"""
Test script for the new CMS API functionality

This script demonstrates:
1. Fetching all data from CMS API without pagination
2. Direct insertion into database
3. Updating the CheckDBUpdate table
"""

import asyncio
import logging
import pandas as pd
from src.data_extraction.cms_api_client import CMSAPIClient
from src.database.mysql_manager import MySQLManager
from src.database.update_checker import UpdateChecker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_new_api_functionality():
    """Test the new API functionality with a sample dataset."""
    
    # Initialize components
    api_client = CMSAPIClient()
    db_manager = MySQLManager()
    update_checker = UpdateChecker(db_manager)
    
    # Test dataset UUID (from the web search results)
    test_uuid = "8c7373f1-dd77-4ed3-bd6c-6abb5b5a44b4"
    table_name = "snf_owners"  # Updated to use new table name
    datayear = "2024-01"  # Example datayear
    
    try:
        logger.info("Testing new API functionality...")
        
        # Test 1: Fetch all data without pagination
        logger.info(f"Testing fetch_all_data for UUID: {test_uuid}")
        data = await api_client.fetch_all_data(test_uuid)
        
        if data:
            logger.info(f"Successfully fetched {len(data)} records")
            logger.info(f"Sample record keys: {list(data[0].keys()) if data else 'No data'}")
        else:
            logger.error("Failed to fetch data")
            return
        
        # Test 2: Fetch and insert data directly into database
        logger.info(f"Testing fetch_and_insert_data for table: {table_name}")
        success = await api_client.fetch_and_insert_data(
            test_uuid, 
            table_name, 
            datayear, 
            db_manager, 
            update_checker
        )
        
        if success:
            logger.info("Successfully fetched and inserted data into database")
            
            # Test 3: Verify CheckDBUpdate table was updated
            last_processed = update_checker.get_last_processed_data(table_name)
            if last_processed:
                last_datayear, last_uuid = last_processed
                logger.info(f"CheckDBUpdate updated: {last_datayear} - {last_uuid}")
            else:
                logger.warning("CheckDBUpdate not found")
        else:
            logger.error("Failed to fetch and insert data")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
    finally:
        # Clean up
        db_manager.close_connection()


async def test_api_without_parameters():
    """Test the API call without offset and size parameters."""
    
    api_client = CMSAPIClient()
    test_uuid = "8c7373f1-dd77-4ed3-bd6c-6abb5b5a44b4"
    
    try:
        logger.info("Testing API call without pagination parameters...")
        
        # This should fetch all records at once
        data = await api_client.fetch_all_data(test_uuid)
        
        if data:
            logger.info(f"Successfully fetched {len(data)} records without pagination")
            logger.info("First few records:")
            for i, record in enumerate(data[:3]):
                logger.info(f"Record {i+1}: {list(record.keys())}")
        else:
            logger.error("Failed to fetch data without pagination")
            
    except Exception as e:
        logger.error(f"Error testing API without parameters: {e}")


async def test_dataframe_cleaning():
    """Test the DataFrame cleaning functionality."""
    
    api_client = CMSAPIClient()
    test_uuid = "8c7373f1-dd77-4ed3-bd6c-6abb5b5a44b4"
    
    try:
        logger.info("Testing DataFrame cleaning functionality...")
        
        # Fetch raw data
        data = await api_client.fetch_all_data(test_uuid)
        
        if data:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            logger.info(f"Original DataFrame shape: {df.shape}")
            logger.info(f"Original DataFrame dtypes: {df.dtypes.value_counts()}")
            
            # Test cleaning
            df_clean = api_client._clean_dataframe(df)
            logger.info(f"Cleaned DataFrame shape: {df_clean.shape}")
            logger.info(f"Cleaned DataFrame dtypes: {df_clean.dtypes.value_counts()}")
            
            # Show sample of cleaned data
            logger.info("Sample of cleaned data:")
            for i, col in enumerate(df_clean.columns[:5]):
                sample_values = df_clean[col].dropna().head(3).tolist()
                logger.info(f"  {col}: {sample_values}")
                
        else:
            logger.error("Failed to fetch data for cleaning test")
            
    except Exception as e:
        logger.error(f"Error testing DataFrame cleaning: {e}")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_api_without_parameters())
    asyncio.run(test_dataframe_cleaning())
    asyncio.run(test_new_api_functionality()) 