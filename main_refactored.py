"""
CMS Data Processing Tool - Main Entry Point

Refactored version using modular architecture for better maintainability
and professional code organization.
"""

import asyncio
import logging

from src.config.settings import Settings
from src.utils.logger import setup_logger
from src.data_processing.dataset_processor import DatasetProcessor
from src.database.mysql_manager import MySQLManager


async def main():
    """
    Main execution function to process multiple CMS datasets and store the results.
    
    Uses the modular architecture for better organization and maintainability.
    """
    # Setup logging
    logger = setup_logger(
        name="cms_processor",
        level=Settings.LOGGING_CONFIG['level'],
        format_string=Settings.LOGGING_CONFIG['format']
    )
    
    logger.info("Starting CMS Data Processing Tool...")
    
    try:
        # Initialize database manager
        db_manager = MySQLManager(
            host=Settings.DB_CONFIG['host'],
            port=Settings.DB_CONFIG['port'],
            user=Settings.DB_CONFIG['user'],
            password=Settings.DB_CONFIG['password'],
            database=Settings.DB_CONFIG['database']
        )
        
        # Initialize dataset processor
        processor = DatasetProcessor(
            csv_folder=Settings.CSV_FOLDER,
            db_manager=db_manager
        )
        
        # Process API-based datasets
        logger.info("Processing API-based datasets...")
        for url in Settings.API_DOCS_URLS:
            success = await processor.process_api_dataset(url)
            if success:
                logger.info(f"Successfully processed API dataset: {url}")
            else:
                logger.error(f"Failed to process API dataset: {url}")
        
        # Process CSV datasets
        logger.info("Processing CSV datasets...")
        for dataset_slug, dataset_id in Settings.CSV_DATASETS.items():
            if dataset_slug == 'state_average':
                success = await processor.process_state_average_dataset()
            else:
                success = await processor.process_csv_dataset(dataset_id, dataset_slug)
            
            if success:
                logger.info(f"Successfully processed CSV dataset: {dataset_slug}")
            else:
                logger.error(f"Failed to process CSV dataset: {dataset_slug}")
        
        logger.info("CMS Data Processing Tool completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise
    finally:
        # Clean up database connection
        if 'db_manager' in locals():
            db_manager.close_connection()


if __name__ == "__main__":
    asyncio.run(main()) 