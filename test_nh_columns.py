#!/usr/bin/env python3
"""
Test script to get actual column names from nh_performance_measures API
"""

import asyncio
import pandas as pd
from src.data_extraction.cms_api_client import CMSAPIClient

async def test_nh_columns():
    """Test to get actual column names from nh_performance_measures API"""
    api_client = CMSAPIClient()
    
    # Use one of the UUIDs from nh_performance_measures
    test_uuid = "74b855fe-c00b-459e-806e-c5f8a9103daa"  # November 2024
    
    print(f"Fetching data for UUID: {test_uuid}")
    
    # Fetch the data
    data = await api_client.fetch_all_data(test_uuid)
    
    if data and len(data) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        print(f"DataFrame shape: {df.shape}")
        print(f"Column names: {list(df.columns)}")
        
        # Show first few rows
        print("\nFirst row:")
        print(df.iloc[0].to_dict())
        
    else:
        print("No data received")

if __name__ == "__main__":
    asyncio.run(test_nh_columns()) 