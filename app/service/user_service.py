# app/service/user_service.py

from app.dao.user_dao import UserDAO

class UserService:
    def get_user(self, user_id):
        """Fetches user information."""
        user = UserDAO.get_user_by_id(user_id)
        if not user:
            raise Exception("User not found")
        return user

    def create_user(self, username, email, password):
        """Creates a new user."""
        UserDAO.create_user(username, email, password)
