# app/dao/user_dao.py

from app.utils.db_connection import get_db_connection

class UserDAO:
    @staticmethod
    def get_user_by_id(user_id):
        """Fetches user data from the MySQL database by user ID."""
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result

    @staticmethod
    def create_user(username, email, password):
        """Creates a new user in the MySQL database."""
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, email, password))
        connection.commit()
        cursor.close()
        connection.close()
