import mysql.connector
from app.config import DATABASE_CONFIG

def get_db_connection():
    """Creates a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database=DATABASE_CONFIG['database']
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def execute_query(query):
    """Executes a query on the database and returns results."""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            connection.close()
            return results
        except mysql.connector.Error as err:
            print(f"Error executing query: {err}")
            connection.close()
    return None
