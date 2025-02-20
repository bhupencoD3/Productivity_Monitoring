# tests/test_user_dao.py

import unittest
from app.dao.user_dao import UserDAO

class TestUserDAO(unittest.TestCase):
    def test_get_user_by_id(self):
        user = UserDAO.get_user_by_id(1)
        self.assertIsNotNone(user)
        self.assertEqual(user['id'], 1)

    def test_create_user(self):
        UserDAO.create_user("testuser", "test@example.com", "password123")
        user = UserDAO.get_user_by_id(2)
        self.assertEqual(user['username'], "testuser")

if __name__ == "__main__":
    unittest.main()
