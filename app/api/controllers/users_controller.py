from app.utils.db_connection import execute_query

def get_all_users():
    query = "SELECT * FROM users;"
    users = execute_query(query)
    if users:
        for user in users:
            print(user)
    else:
        print("No users found.")
