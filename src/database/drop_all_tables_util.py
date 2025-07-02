import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.mysql_manager import MySQLManager

if __name__ == "__main__":
    db_manager = MySQLManager()
    conn = db_manager.get_connection()
    if conn:
        success = db_manager.drop_all_tables()
        if success:
            print("All tables dropped successfully.")
        else:
            print("Failed to drop all tables. See logs for details.")
        db_manager.close_connection()
    else:
        print("Could not connect to the database.") 