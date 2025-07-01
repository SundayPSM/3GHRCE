"""
MySQL Database Manager

Handles all MySQL database operations including connection management,
table creation, and data insertion for the CMS Data Processing Tool.
"""

import logging
import mysql.connector
from mysql.connector import Error
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class MySQLManager:
    """Manages MySQL database connections and operations."""
    
    def __init__(self, host: str = 'localhost', port: int = 3306, 
                 user: str = 'root', password: str = 'Nithin@123', 
                 database: str = 'cms_data'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def get_connection(self) -> Optional[mysql.connector.MySQLConnection]:
        """
        Establishes a connection to the MySQL database. 
        Creates the database if it doesn't exist.

        Returns:
            mysql.connector.connection.MySQLConnection: A MySQL connection object if successful, else None.
        """
        try:
            # First connect without database to create it if needed
            initial_config = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'raise_on_warnings': False
            }
            logger.info("Attempting to connect to MySQL server...")
            initial_connection = mysql.connector.connect(**initial_config)
            
            # Create database if it doesn't exist
            cursor = initial_connection.cursor()
            try:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                logger.info(f"Database {self.database} is ready.")
            except Error as e:
                if e.errno == 1007:  # Database exists error
                    logger.info(f"Database {self.database} already exists.")
                else:
                    raise
            cursor.close()
            initial_connection.close()
            
            # Now connect with the database
            config = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'password': self.password,
                'raise_on_warnings': False
            }
            logger.info(f"Connecting to {self.database} database...")
            self.connection = mysql.connector.connect(**config)
            if self.connection.is_connected():
                logger.info(f"Connected to MySQL database {self.database}.")
                return self.connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return None
    
    def create_table(self, table_name: str, df: pd.DataFrame) -> bool:
        """
        Creates a table in the MySQL database using the DataFrame schema.
        All columns are forced to TEXT type for consistency.

        Args:
            table_name (str): Name of the table to create.
            df (pandas.DataFrame): DataFrame whose schema is used to define the table.

        Returns:
            bool: True if table created successfully, False otherwise.
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
            
        cursor = self.connection.cursor()
        try:
            logger.info(f"Creating table {table_name} in database {self.database}")
            
            # Drop table if exists
            try:
                cursor.execute(f"DROP TABLE IF EXISTS `{self.database}`.`{table_name}`")
                logger.info(f"Dropped existing table {table_name} if it existed")
            except Error as e:
                logger.warning(f"Warning while dropping table {table_name}: {e}")

            # Rename long columns to fit MySQL constraints
            df_clean = self._sanitize_column_names(df)
            
            # Force all columns to string (TEXT)
            for col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str)

            columns = [f"`{col}` TEXT" for col in df_clean.columns]
            create_table_query = f"""
            CREATE TABLE `{self.database}`.`{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                {', '.join(columns)},
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            self.connection.commit()
            logger.info(f"Table `{table_name}` created successfully with {len(columns)} columns")
            return True
        except Error as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
        finally:
            cursor.close()
    
    def insert_data(self, table_name: str, df: pd.DataFrame) -> bool:
        """
        Inserts the data from the DataFrame into the specified MySQL table.

        Args:
            table_name (str): Target table name.
            df (pandas.DataFrame): DataFrame to insert into the database.

        Returns:
            bool: True if data inserted successfully, False otherwise.
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
            
        cursor = self.connection.cursor()
        try:
            columns = [f"`{col}`" for col in df.columns]
            placeholders = ", ".join(["%s"] * len(columns))
            insert_query = f"INSERT INTO `{self.database}`.`{table_name}` ({', '.join(columns)}) VALUES ({placeholders})"

            # Replace NaN with empty strings to avoid NULL issues
            values = [tuple(row) for row in df.fillna("").values]

            cursor.executemany(insert_query, values)
            self.connection.commit()
            logger.info(f"{len(values)} rows inserted into `{table_name}`.")
            return True
        except Exception as e:
            logger.error(f"Error inserting data into `{table_name}`: {e}")
            return False
        finally:
            cursor.close()
    
    def _sanitize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sanitizes DataFrame column names to fit MySQL constraints.
        
        Args:
            df (pd.DataFrame): Original DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with sanitized column names
        """
        col_name_map = {}
        used_names = set()
        
        for col in df.columns:
            if len(col) > 64:
                base = col[:60]
                suffix = 1
                new_col = f"{base}_{suffix}"
                while new_col in used_names:
                    suffix += 1
                    new_col = f"{base}_{suffix}"
                col_name_map[col] = new_col
                used_names.add(new_col)
            else:
                col_name_map[col] = col
                used_names.add(col)
        
        if col_name_map:
            logger.info(f"Renamed {len(col_name_map)} columns to fit MySQL constraints")
            return df.rename(columns=col_name_map)
        
        return df
    
    def close_connection(self):
        """Closes the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed.")
            self.connection = None 