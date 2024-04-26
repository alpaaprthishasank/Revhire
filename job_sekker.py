import sqlite3
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_db_connection():
    return sqlite3.connect("job_portal.db")

def create_job_seeker_in_db(cursor, conn, job_seeker):
    # Hash the password
    cursor.execute("SELECT * FROM job_seeker WHERE email=?", (job_seeker.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(job_seeker.password)

    # Insert job seeker data into the database
    cursor.execute(
        "INSERT INTO job_seeker (name, email, phone, password) VALUES (?, ?, ?, ?)",
        (job_seeker.name, job_seeker.email, job_seeker.phone, hashed_password),
    )
    conn.commit()
