"""
Page Inspector

Helps inspect the HTML structure of CMS data pages to identify tables
and their content for debugging scraping issues.
"""

import logging
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Page
import asyncio

logger = logging.getLogger(__name__)


class PageInspector:
    """Inspector for analyzing page structure and content."""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def inspect_page_tables(self, page_url: str) -> Dict[str, Any]:
        """
        Inspects all tables on a page and provides detailed information.

        Args:
            page_url (str): URL of the page to inspect.

        Returns:
            Dict[str, Any]: Detailed information about all tables found.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                logger.info(f"Inspecting page: {page_url}")
                await page.goto(page_url, wait_until="networkidle")
                await page.wait_for_timeout(5000)
                
                return await self._analyze_page_tables(page)
                
            except Exception as e:
                logger.error(f"Error inspecting page: {e}")
                return {}
            finally:
                await browser.close()
    
    async def _analyze_page_tables(self, page: Page) -> Dict[str, Any]:
        """
        Analyzes all tables on the page.

        Args:
            page (Page): Playwright page object.

        Returns:
            Dict[str, Any]: Analysis results.
        """
        try:
            # Find all tables
            tables = page.locator("table")
            table_count = await tables.count()
            
            logger.info(f"Found {table_count} tables on the page")
            
            analysis = {
                "total_tables": table_count,
                "tables": []
            }
            
            for i in range(table_count):
                table = tables.nth(i)
                table_info = await self._analyze_table(page, table, i)
                analysis["tables"].append(table_info)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing tables: {e}")
            return {"error": str(e)}
    
    async def _analyze_table(self, page: Page, table, index: int) -> Dict[str, Any]:
        """
        Analyzes a single table.

        Args:
            page (Page): Playwright page object.
            table: Table element.
            index (int): Table index.

        Returns:
            Dict[str, Any]: Table analysis.
        """
        try:
            # Get table attributes
            table_html = await table.inner_html()
            table_text = await table.text_content()
            
            # Get table classes
            table_classes = await table.get_attribute("class") or ""
            
            # Get parent element info
            parent = table.locator("xpath=..")
            parent_tag = await parent.evaluate("el => el.tagName.toLowerCase()")
            parent_classes = await parent.get_attribute("class") or ""
            
            # Count rows and columns
            rows = table.locator("tr")
            row_count = await rows.count()
            
            headers = table.locator("th, td")
            col_count = await headers.count()
            
            # Check for specific content
            has_dataset_versions = "dataset versions" in table_text.lower()
            has_version = "version" in table_text.lower()
            has_table_sm = "table-sm" in table_classes
            has_table_bordered = "table-bordered" in table_classes
            
            table_info = {
                "index": index,
                "classes": table_classes,
                "parent_tag": parent_tag,
                "parent_classes": parent_classes,
                "row_count": row_count,
                "col_count": col_count,
                "has_dataset_versions": has_dataset_versions,
                "has_version": has_version,
                "has_table_sm": has_table_sm,
                "has_table_bordered": has_table_bordered,
                "text_preview": table_text[:200] + "..." if len(table_text) > 200 else table_text,
                "html_preview": table_html[:500] + "..." if len(table_html) > 500 else table_html
            }
            
            logger.info(f"Table {index}: {row_count} rows, {col_count} cols, "
                       f"Dataset Versions: {has_dataset_versions}, "
                       f"Classes: {table_classes}")
            
            return table_info
            
        except Exception as e:
            logger.error(f"Error analyzing table {index}: {e}")
            return {"index": index, "error": str(e)}
    
    async def find_dataset_versions_table(self, page_url: str) -> Dict[str, Any]:
        """
        Specifically looks for the Dataset Versions table.

        Args:
            page_url (str): URL of the page to inspect.

        Returns:
            Dict[str, Any]: Information about the Dataset Versions table.
        """
        analysis = await self.inspect_page_tables(page_url)
        
        # Find tables that might be the Dataset Versions table
        potential_tables = []
        
        for table in analysis.get("tables", []):
            if table.get("has_dataset_versions") or table.get("has_version"):
                potential_tables.append(table)
        
        return {
            "analysis": analysis,
            "potential_dataset_versions_tables": potential_tables
        }


async def main():
    """Test function to inspect the page."""
    inspector = PageInspector()
    
    test_url = "https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/skilled-nursing-facility-all-owners/api-docs"
    
    print(f"Inspecting page: {test_url}")
    print("-" * 80)
    
    result = await inspector.find_dataset_versions_table(test_url)
    
    print(f"Found {result['analysis']['total_tables']} total tables")
    print(f"Found {len(result['potential_dataset_versions_tables'])} potential Dataset Versions tables")
    
    for table in result['potential_dataset_versions_tables']:
        print(f"\n📋 Table {table['index']}:")
        print(f"   Classes: {table['classes']}")
        print(f"   Parent: {table['parent_tag']} with classes: {table['parent_classes']}")
        print(f"   Rows: {table['row_count']}, Columns: {table['col_count']}")
        print(f"   Has Dataset Versions: {table['has_dataset_versions']}")
        print(f"   Has Version: {table['has_version']}")
        print(f"   Text Preview: {table['text_preview']}")


if __name__ == "__main__":
    asyncio.run(main()) 