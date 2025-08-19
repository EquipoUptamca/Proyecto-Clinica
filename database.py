import pyodbc
import logging
from config import SERVER, DATABASE, USE_WINDOWS_AUTH, USERNAME, PASSWORD

# Function to get a database connection
def get_db_connection():
    try:
        if USE_WINDOWS_AUTH:
            connection_string = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={SERVER};DATABASE={DATABASE};'
                'Trusted_Connection=yes;'
            )
        else:
            connection_string = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={SERVER};DATABASE={DATABASE};'
                f'UID={USERNAME};PWD={PASSWORD}'
            )
        
        conn = pyodbc.connect(connection_string)
        logging.info("Database connection established successfully")
        return conn
    except pyodbc.Error as e:
        logging.error(f"Database connection failed: {str(e)}")
        return None