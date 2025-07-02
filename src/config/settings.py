"""
Settings Configuration

Central configuration management for the CMS Data Processing Tool.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings and configuration."""
    
    # Database configuration
    DB_CONFIG: Dict[str, Any] = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'mysql123'),
        'database': os.getenv('DB_NAME', 'cms_data'),
        'raise_on_warnings': False
    }
    
    # API configuration
    API_CONFIG = {
        'timeout': 300.0,  # 5 minutes
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
    
    # Mapping from API docs URLs to table names
    URL_TO_TABLE_MAP = {
        "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-all-owners/api-docs": "snf_owners",
        "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-enrollments/api-docs": "snf_enrollments",
        "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-change-of-ownership/api-docs": "snf_ownership_changes",
        "https://data.cms.gov/quality-of-care/nursing-home-affiliated-entity-performance-measures/api-docs": "nh_performance_measures"
    }
    
    # Column mapping from API response names to database column names
    COLUMN_MAPPINGS = {
        'nh_performance_measures': {
            'Average percentage of short-stay residents who were re-hospitalized after a nursing home admission': 'Avg pct short-stay residents re-hospitalized after admission',
            'Average percentage of short-stay residents who have had an outpatient emergency department visit': 'Avg pct short-stay residents with outpatient ED visit',
            'Average percentage of short-stay residents who newly received an antipsychotic medication': 'Avg pct short-stay residents newly received antipsychotic',
            'Average percentage of short-stay residents with pressure ulcers or pressure injuries that are new or worsened': 'Avg pct short-stay residents with new/worsened pressure ulcers',
            'Average percentage of short-stay residents who made improvements in function': 'Avg pct short-stay residents made improvements in function',
            'Average percentage of short-stay residents who were assessed and appropriately given the seasonal influenza vaccine': 'Avg pct short-stay residents given influenza vaccine',
            'Average percentage of short-stay residents who were assessed and appropriately given the  pneumococcal vaccine': 'Avg pct short-stay residents given pneumococcal vaccine',
            'Average number of hospitalizations per 1,000 long-stay resident days': 'Avg number hospitalizations per 1000 long-stay resident days',
            'Average number of outpatient emergency department visits per 1,000 long-stay resident days': 'Avg number outpatient ED visits per 1000 long-stay resident days',
            'Average percentage of long-stay residents who received an antipsychotic medication': 'Avg pct long-stay residents received antipsychotic medication',
            'Average percentage of long-stay residents experiencing one or more falls with major injury': 'Avg pct long-stay residents with falls with major injury',
            'Average percentage of long-stay high-risk residents with pressure ulcers': 'Avg pct long-stay high-risk residents with pressure ulcers',
            'Average percentage of long-stay residents with a urinary tract infection': 'Avg pct long-stay residents with urinary tract infection',
            'Average percentage of long-stay residents who have or had a catheter inserted and left in their bladder': 'Avg pct long-stay residents with catheter inserted',
            'Average percentage of long-stay residents whose ability to move independently worsened': 'Avg pct long-stay residents ability to move worsened',
            'Average percentage of long-stay residents whose need for help with activities of daily living has increased': 'Avg pct long-stay residents need for ADL help increased',
            'Average percentage of long-stay residents who were assessed and appropriately given the seasonal influenza vaccine': 'Avg pct long-stay residents given influenza vaccine',
            'Average percentage of long-stay residents who were assessed and appropriately given the  pneumococcal vaccine': 'Avg pct long-stay residents given pneumococcal vaccine',
            'Average percentage of long-stay residents who were physically restrained': 'Avg pct long-stay residents physically restrained',
            'Average percentage of long-stay low-risk residents who lose control of their bowels or bladder': 'Avg pct long-stay low-risk residents lose control bowels/bladder',
            'Average percentage of long-stay residents who lose too much weight': 'Avg pct long-stay residents who lose too much weight',
            'Average percentage of long-stay residents who have symptoms of depression': 'Avg pct long-stay residents with symptoms of depression',
            'Average percentage of long-stay residents who used antianxiety or hypnotic medication': 'Avg pct long-stay residents used antianxiety/hypnotic medication',
            'Average rate of potentially preventable hospital readmissions 30 days after discharge from a SNF': 'Avg rate potentially preventable hospital readmissions 30 days',
            'Average percentage of current residents up to date with COVID-19 vaccines': 'Avg pct current residents up to date with COVID-19 vaccines',
            'Average percentage of healthcare personnel up to date with COVID-19 vaccines': 'Avg pct healthcare personnel up to date with COVID-19 vaccines'
        }
    }
    
    # Predefined table schemas to ensure consistent column structure
    TABLE_SCHEMAS = {
        'snf_owners': [
            'datayear',
            'ENROLLMENT ID', 'ASSOCIATE ID', 'ORGANIZATION NAME', 'ASSOCIATE ID - OWNER',
            'TYPE - OWNER', 'ROLE CODE - OWNER', 'ROLE TEXT - OWNER', 'ASSOCIATION DATE - OWNER',
            'FIRST NAME - OWNER', 'MIDDLE NAME - OWNER', 'LAST NAME - OWNER', 'TITLE - OWNER',
            'ORGANIZATION NAME - OWNER', 'DOING BUSINESS AS NAME - OWNER', 'ADDRESS LINE 1 - OWNER',
            'ADDRESS LINE 2 - OWNER', 'CITY - OWNER', 'STATE - OWNER', 'ZIP CODE - OWNER',
            'PERCENTAGE OWNERSHIP', 'CREATED FOR ACQUISITION - OWNER', 'CORPORATION - OWNER',
            'LLC - OWNER', 'MEDICAL PROVIDER SUPPLIER - OWNER', 'MANAGEMENT SERVICES COMPANY - OWNER',
            'MEDICAL STAFFING COMPANY - OWNER', 'HOLDING COMPANY - OWNER', 'INVESTMENT FIRM - OWNER',
            'FINANCIAL INSTITUTION - OWNER', 'CONSULTING FIRM - OWNER', 'FOR PROFIT - OWNER',
            'NON PROFIT - OWNER', 'PRIVATE EQUITY COMPANY - OWNER', 'REIT - OWNER',
            'CHAIN HOME OFFICE - OWNER', 'TRUST OR TRUSTEE - OWNER', 'OTHER TYPE - OWNER',
            'OTHER TYPE TEXT - OWNER', 'PARENT COMPANY - OWNER', 'OWNED BY ANOTHER ORG OR IND - OWNER'
        ],
        'snf_enrollments': [
            'datayear',
            'ENROLLMENT ID', 'ENROLLMENT STATE', 'PROVIDER TYPE CODE', 'PROVIDER TYPE TEXT',
            'NPI', 'MULTIPLE NPI FLAG', 'CCN', 'ASSOCIATE ID', 'ORGANIZATION NAME',
            'DOING BUSINESS AS NAME', 'INCORPORATION DATE', 'INCORPORATION STATE',
            'ORGANIZATION TYPE STRUCTURE', 'ORGANIZATION OTHER TYPE TEXT', 'PROPRIETARY_NONPROFIT',
            'NURSING HOME PROVIDER NAME', 'AFFILIATION ENTITY NAME', 'AFFILIATION ENTITY ID',
            'ADDRESS LINE 1', 'ADDRESS LINE 2', 'CITY', 'STATE', 'ZIP CODE'
        ],
        'snf_ownership_changes': [
            'datayear',
            'ENROLLMENT ID - BUYER', 'ENROLLMENT STATE - BUYER', 'PROVIDER TYPE CODE - BUYER',
            'PROVIDER TYPE TEXT - BUYER', 'NPI - BUYER', 'MULTIPLE NPI FLAG - BUYER',
            'CCN - BUYER', 'ASSOCIATE ID - BUYER', 'ORGANIZATION NAME - BUYER',
            'DOING BUSINESS AS NAME - BUYER', 'CHOW TYPE CODE', 'CHOW TYPE TEXT', 'EFFECTIVE DATE',
            'ENROLLMENT ID - SELLER', 'ENROLLMENT STATE - SELLER', 'PROVIDER TYPE CODE - SELLER',
            'PROVIDER TYPE TEXT - SELLER', 'NPI - SELLER', 'MULTIPLE NPI FLAG - SELLER',
            'CCN - SELLER', 'ASSOCIATE ID - SELLER', 'ORGANIZATION NAME - SELLER',
            'DOING BUSINESS AS NAME - SELLER'
        ],
        'nh_performance_measures': [
            'datayear',
            'Affiliated entity', 'Affiliated entity ID', 'Number of facilities',
            'Number of states and territories with operations', 'Number of Special Focus Facilities (SFF)',
            'Number of SFF candidates', 'Number of facilities with an abuse icon',
            'Percentage of facilities with an abuse icon', 'Percent of facilities classified as for-profit',
            'Percent of facilities classified as non-profit', 'Percent of facilities classified as government-owned',
            'Average overall 5-star rating', 'Average health inspection rating', 'Average staffing rating',
            'Average quality rating', 'Average total nurse hours per resident day',
            'Average total weekend nurse hours per resident day', 'Average total Registered Nurse hours per resident day',
            'Average total nursing staff turnover percentage', 'Average Registered Nurse turnover percentage',
            'Average number of administrators who have left the nursing home', 'Total number of fines',
            'Average number of fines', 'Total amount of fines in dollars', 'Average amount of fines in dollars',
            'Total number of payment denials', 'Average number of payment denials',
            'Avg pct short-stay residents re-hospitalized after admission',
            'Avg pct short-stay residents with outpatient ED visit',
            'Avg pct short-stay residents newly received antipsychotic',
            'Avg pct short-stay residents with new/worsened pressure ulcers',
            'Avg pct short-stay residents made improvements in function',
            'Avg pct short-stay residents given influenza vaccine',
            'Avg pct short-stay residents given pneumococcal vaccine',
            'Avg number hospitalizations per 1000 long-stay resident days',
            'Avg number outpatient ED visits per 1000 long-stay resident days',
            'Avg pct long-stay residents received antipsychotic medication',
            'Avg pct long-stay residents with falls with major injury',
            'Avg pct long-stay high-risk residents with pressure ulcers',
            'Avg pct long-stay residents with urinary tract infection',
            'Avg pct long-stay residents with catheter inserted',
            'Avg pct long-stay residents ability to move worsened',
            'Avg pct long-stay residents need for ADL help increased',
            'Avg pct long-stay residents given influenza vaccine',
            'Avg pct long-stay residents given pneumococcal vaccine',
            'Avg pct long-stay residents physically restrained',
            'Avg pct long-stay low-risk residents lose control bowels/bladder',
            'Avg pct long-stay residents who lose too much weight',
            'Avg pct long-stay residents with symptoms of depression',
            'Avg pct long-stay residents used antianxiety/hypnotic medication',
            'Avg rate potentially preventable hospital readmissions 30 days',
            'Avg pct current residents up to date with COVID-19 vaccines',
            'Avg pct healthcare personnel up to date with COVID-19 vaccines'
        ]
    } 