# app/db_setup.py
import mysql.connector
from config import DB_CONFIG
from utils.db_connection import get_db_connection, close_db_connection


def initialize_database():
    # Connect without specifying database to create it
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"]
    )
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS productivity_db")
        print("Database 'productivity_db' created or already exists")
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        cursor.close()
        conn.close()

    # Connect to productivity_db to create tables
    conn = get_db_connection()  # Uses DB_CONFIG with database specified
    if conn is None:
        print("Failed to connect to productivity_db")
        return
    cursor = conn.cursor()
    try:
        # Create employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                face_image BLOB,
                face_image_path VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create productivity_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productivity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                duration FLOAT NOT NULL,
                log_date DATE NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        """)

        # Create frame_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frame_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                frame_path VARCHAR(255) NOT NULL,
                timestamp DATETIME NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        """)

        conn.commit()
        print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        close_db_connection(conn)


if __name__ == "__main__":
    initialize_database()
