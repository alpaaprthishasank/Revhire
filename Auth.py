from database import get_db_connection
import sqlite3
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def authenticate_user(username: str, password: str, user_type: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_type == "job_seeker":
        cursor.execute("SELECT * FROM job_seeker WHERE email=?", (username,))
    elif user_type == "employer":
        cursor.execute("SELECT * FROM employer WHERE email=?", (username,))

    user = cursor.fetchone()
    if user_type=="job_seeker":
        if user:
            stored_password = user[4]  # Password is stored in the fifth column
        if pwd_context.verify(password, stored_password):
            return user
    elif user_type=="employer":
        if user:
            stored_password = user[5]  # Password is stored in the fifth column
        if pwd_context.verify(password, stored_password):
            return user
    return None
