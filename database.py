import sqlite3
db_file = 'job_portal.db'

def get_db_connection():
    conn = sqlite3.connect(db_file)
    return conn