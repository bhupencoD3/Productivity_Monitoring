# app/utils/db_connection.py
import mysql.connector
from config import DB_CONFIG


def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def close_db_connection(connection):
    if connection and connection.is_connected():
        connection.close()

