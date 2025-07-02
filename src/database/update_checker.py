"""
Database Update Checker

Handles the CheckDBUpdate table logic to determine which datasets need updating.
Compares current scraped UUIDs with previously processed UUIDs to avoid unnecessary API calls.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Manages database update tracking using CheckDBUpdate table."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.check_table_name = "CheckDBUpdate"
    
    def create_check_table(self) -> bool:
        """
        Creates the CheckDBUpdate table if it doesn't exist.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                logger.error("Could not get database connection")
                return False
            
            cursor = conn.cursor()
            
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.check_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                TableName VARCHAR(255) NOT NULL,
                datayear VARCHAR(50) NOT NULL,
                UUID VARCHAR(36) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_table (TableName)
            )
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
            
            logger.info(f"CheckDBUpdate table created/verified successfully")
            return True
            
        except Error as e:
            logger.error(f"Error creating CheckDBUpdate table: {e}")
            return False
    
    def get_last_processed_data(self, table_name: str) -> Optional[Tuple[str, str]]:
        """
        Gets the last processed datayear and UUID for a specific table.
        
        Args:
            table_name (str): Name of the table to check.
            
        Returns:
            Optional[Tuple[str, str]]: (datayear, UUID) if found, None otherwise.
        """
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            select_sql = f"""
            SELECT datayear, UUID 
            FROM {self.check_table_name} 
            WHERE TableName = %s
            """
            
            cursor.execute(select_sql, (table_name,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                logger.info(f"Found last processed data for {table_name}: {result[0]} - {result[1]}")
                return result[0], result[1]
            else:
                logger.info(f"No previous data found for {table_name}")
                return None
                
        except Error as e:
            logger.error(f"Error getting last processed data for {table_name}: {e}")
            return None
    
    def update_processed_data(self, table_name: str, datayear: str, uuid: str) -> bool:
        """
        Updates or inserts the processed data for a table.
        
        Args:
            table_name (str): Name of the table.
            datayear (str): Year/month of the data.
            uuid (str): UUID of the processed data.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Use INSERT ... ON DUPLICATE KEY UPDATE for upsert
            upsert_sql = f"""
            INSERT INTO {self.check_table_name} (TableName, datayear, UUID) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                datayear = VALUES(datayear),
                UUID = VALUES(UUID),
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(upsert_sql, (table_name, datayear, uuid))
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated CheckDBUpdate for {table_name}: {datayear} - {uuid}")
            return True
            
        except Error as e:
            logger.error(f"Error updating CheckDBUpdate for {table_name}: {e}")
            return False
    
    def determine_update_needs(self, scraped_data: Dict[str, List[Tuple[str, str]]]) -> Dict[str, List[str]]:
        """
        Determines which datasets need updating based on scraped data vs CheckDBUpdate.
        
        Args:
            scraped_data: Dict[table_name, List[Tuple[datayear, uuid]]] - Current scraped data.
            
        Returns:
            Dict[str, List[str]]: Dict[table_name, List[uuid_to_fetch]] - UUIDs that need fetching.
        """
        update_needs = {}
        
        for table_name, version_list in scraped_data.items():
            if not version_list:
                logger.warning(f"No scraped data for {table_name}")
                continue
            
            # Get the latest (first) UUID from scraped data
            latest_datayear, latest_uuid = version_list[0]
            
            # Check what was last processed
            last_processed = self.get_last_processed_data(table_name)
            
            if last_processed is None:
                # First time processing this table - fetch all 6 months
                logger.info(f"First time processing {table_name} - fetching all 6 months")
                uuids_to_fetch = [uuid for _, uuid in version_list]
                update_needs[table_name] = uuids_to_fetch
                
            else:
                last_datayear, last_uuid = last_processed
                
                if latest_uuid == last_uuid:
                    # No new data - skip this table
                    logger.info(f"No new data for {table_name} (latest: {latest_uuid})")
                    continue
                
                # New data available - determine what to fetch
                logger.info(f"New data available for {table_name}: {latest_uuid} vs {last_uuid}")
                
                # Find UUIDs to fetch (from latest back to last processed)
                uuids_to_fetch = []
                for datayear, uuid in version_list:
                    uuids_to_fetch.append(uuid)
                    if uuid == last_uuid:
                        break
                
                if uuids_to_fetch:
                    update_needs[table_name] = uuids_to_fetch
                    logger.info(f"Will fetch {len(uuids_to_fetch)} versions for {table_name}")
        
        return update_needs
    
    def get_all_tracked_tables(self) -> List[str]:
        """
        Gets all table names currently tracked in CheckDBUpdate.
        
        Returns:
            List[str]: List of table names.
        """
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            select_sql = f"SELECT TableName FROM {self.check_table_name}"
            cursor.execute(select_sql)
            results = cursor.fetchall()
            cursor.close()
            
            return [row[0] for row in results]
            
        except Error as e:
            logger.error(f"Error getting tracked tables: {e}")
            return []
    
    def cleanup_orphaned_records(self, current_tables: List[str]) -> bool:
        """
        Removes records for tables that no longer exist in current processing.
        
        Args:
            current_tables (List[str]): List of tables currently being processed.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            tracked_tables = self.get_all_tracked_tables()
            orphaned_tables = [table for table in tracked_tables if table not in current_tables]
            
            if not orphaned_tables:
                return True
            
            conn = self.db_manager.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            for table_name in orphaned_tables:
                delete_sql = f"DELETE FROM {self.check_table_name} WHERE TableName = %s"
                cursor.execute(delete_sql, (table_name,))
                logger.info(f"Removed orphaned record for {table_name}")
            
            conn.commit()
            cursor.close()
            return True
            
        except Error as e:
            logger.error(f"Error cleaning up orphaned records: {e}")
            return False 