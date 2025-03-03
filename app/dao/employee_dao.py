# app/dao/employee_dao.py (Updated with get_all_employees)
import mysql.connector
from app.utils.db_connection import (
    get_db_connection,
    close_db_connection,
)  # Adjusted import path


class EmployeeDAO:
    def add_employee(self, name, face_image_path=None, face_image_data=None):
        conn = get_db_connection()
        if conn is None:
            return None
        cursor = conn.cursor()
        try:
            # Check if name exists
            cursor.execute("SELECT employee_id FROM employees WHERE name = %s", (name,))
            existing = cursor.fetchone()
            if existing:
                print(f"Employee {name} already exists with ID {existing[0]}")
                return existing[0]

            if face_image_data:
                cursor.execute(
                    "INSERT INTO employees (name, face_image) VALUES (%s, %s)",
                    (name, face_image_data),
                )
            else:
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

    def get_all_employees(self):
        """
        Fetch all employees from the employees table.
        """
        conn = get_db_connection()
        if conn is None:
            print("Failed to connect to database")
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT employee_id, name, face_image_path FROM employees")
            employees = cursor.fetchall()
            return employees
        except Exception as e:
            print(f"Error fetching all employees: {e}")
            return []
        finally:
            cursor.close()
            close_db_connection(conn)
