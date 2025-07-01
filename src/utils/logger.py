"""
Logger Utility

Centralized logging configuration for the CMS Data Processing Tool.
"""

import logging
from typing import Optional


def setup_logger(name: str = __name__, level: str = 'INFO', 
                format_string: Optional[str] = None) -> logging.Logger:
    """
    Sets up a logger with the specified configuration.
    
    Args:
        name (str): Logger name
        level (str): Logging level
        format_string (Optional[str]): Custom format string
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create console handler if it doesn't exist
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(format_string)
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Gets a logger instance with default configuration.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return setup_logger(name) 