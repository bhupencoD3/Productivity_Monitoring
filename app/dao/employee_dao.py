# app/dao/employee_dao.py
import mysql.connector
from utils.db_connection import get_db_connection, close_db_connection


class EmployeeDAO:
    def add_employee(self, name, face_image_path=None, face_image_data=None):
        conn = get_db_connection()
        if conn is None:
            return None
        cursor = conn.cursor()
        try:
            if face_image_data:  # Store image as BLOB
                cursor.execute(
                    "INSERT INTO employees (name, face_image) VALUES (%s, %s)",
                    (name, face_image_data),
                )
            else:  # Store image path
                cursor.execute(
                    "INSERT INTO employees (name, face_image_path) VALUES (%s, %s)",
                    (name, face_image_path),
                )
            conn.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            employee_id = cursor.fetchone()[0]
            return employee_id
        except Exception as e:
            print(f"Error adding employee: {e}")
            return None
        finally:
            cursor.close()
            close_db_connection(conn)

    def get_employee_by_id(self, employee_id):
        conn = get_db_connection()
        if conn is None:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM employees WHERE employee_id = %s", (employee_id,)
            )
            return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching employee: {e}")
            return None
        finally:
            cursor.close()
            close_db_connection(conn)

    def log_productivity(self, employee_id, start_time, end_time, duration):
        conn = get_db_connection()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO productivity_logs (employee_id, start_time, end_time, duration, log_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (employee_id, start_time, end_time, duration, start_time.date()),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging productivity: {e}")
            return False
        finally:
            cursor.close()
            close_db_connection(conn)

    def log_frame(self, employee_id, frame_path, timestamp):
        conn = get_db_connection()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO frame_logs (employee_id, frame_path, timestamp) VALUES (%s, %s, %s)",
                (employee_id, frame_path, timestamp),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging frame: {e}")
            return False
        finally:
            cursor.close()
            close_db_connection(conn)

