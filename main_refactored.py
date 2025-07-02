"""
CMS Data Processing Tool - Main Entry Point

Refactored version using modular architecture for better maintainability
and professional code organization.
"""

import asyncio
import logging

from src.config.settings import Settings
from src.utils.logger import setup_logger
from src.data_processing.dataset_orchestrator import DatasetOrchestrator


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
        orchestrator = DatasetOrchestrator()
        success = await orchestrator.run_complete_pipeline()
        if success:
            logger.info("Pipeline completed successfully!")
        else:
            logger.error("Pipeline encountered errors.")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 