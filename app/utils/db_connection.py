# app/utils/db_connection.py
import mysql.connector
from app.config import DB_CONFIG


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            port=DB_CONFIG["port"],
            ssl_ca=DB_CONFIG["ssl_ca"],
            ssl_verify_cert=True,  # Enforce certificate verification
        )
        return connection
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def close_db_connection(connection):
    if connection and connection.is_connected():
        connection.close()
