"""
Dataset Versions Scraper

Extracts the "Dataset Versions" table from CMS data pages using Playwright.
This scraper waits for the page to fully load and then extracts the table data.
"""

import logging
import pandas as pd
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Page
import asyncio

logger = logging.getLogger(__name__)


class DatasetVersionsScraper:
    """Scraper for extracting Dataset Versions table from CMS data pages."""
    
    def __init__(self, timeout: float = 300.0):  # 5 minutes
        self.timeout = timeout
    
    async def scrape(self, url: str) -> pd.DataFrame:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
            # Wait for the "Dataset Versions" heading and table to appear
            await page.wait_for_selector("h3:text('Dataset Versions') + table.table.table-sm.table-bordered", timeout=self.timeout * 1000)
            # Select the table right after the heading
            table = page.locator("h3:text('Dataset Versions') + table.table.table-sm.table-bordered")
            # Extract headers
            headers = await table.locator("thead tr th").all_text_contents()
            # Extract rows
            rows = []
            for row in await table.locator("tbody tr").all():
                cells = await row.locator("td").all_text_contents()
                rows.append(cells)
            await browser.close()
            return pd.DataFrame(rows, columns=headers)
    
    async def save_to_csv(self, df: pd.DataFrame, filename: str) -> bool:
        """
        Saves the scraped data to a CSV file.

        Args:
            df (pd.DataFrame): DataFrame to save.
            filename (str): Output filename.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            df.to_csv(filename, index=False)
            logger.info(f"Data saved to CSV: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return False


async def main():
    """Test function to demonstrate the scraper."""
    url = "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-all-owners/api-docs"
    scraper = DatasetVersionsScraper()
    df = await scraper.scrape(url)
    print(df)
    df.to_csv("dataset_versions.csv", index=False)


if __name__ == "__main__":
    asyncio.run(main()) 