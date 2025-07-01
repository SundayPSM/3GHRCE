"""
Settings Configuration

Central configuration management for the CMS Data Processing Tool.
"""

import os
from typing import Dict, Any, List


class Settings:
    """Application settings and configuration."""
    
    # Database configuration
    DB_CONFIG: Dict[str, Any] = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'Nithin@123'),
        'database': os.getenv('DB_NAME', 'cms_data'),
        'raise_on_warnings': False
    }
    
    # API configuration
    API_CONFIG = {
        'timeout': 30.0,
        'page_size': 5000,
        'max_pages': 10
    }
    
    # File paths
    CSV_FOLDER = "csv"
    
    # CMS API URLs for different datasets
    API_DOCS_URLS: List[str] = [
        # 1. SNF All Owners
        "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-all-owners/api-docs",
        
        # 2. SNF Enrollments
        "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-enrollments/api-docs",
        
        # 3. SNF Change of Ownership
        "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-change-of-ownership/api-docs",
        
        # 4. SNF Entity Performance
        "https://data.cms.gov/quality-of-care/nursing-home-affiliated-entity-performance-measures/api-docs",
        
        # 5. SNF Cost Report (API-based method)
        "https://data.cms.gov/provider-compliance/cost-report/skilled-nursing-facility-cost-report/api-docs"
    ]
    
    # CSV Dataset IDs
    CSV_DATASETS: Dict[str, str] = {
        'provider': '4pq5-n9py',
        'state_average': 'xcdc-v8bm'
    }
    
    # Logging configuration
    LOGGING_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    } 