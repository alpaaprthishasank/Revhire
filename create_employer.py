import sqlite3
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException
from database import get_db_connection
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
conn = get_db_connection()
cursor = conn.cursor()

def create_employer_in_db(employer):
    cursor.execute("SELECT * FROM employer WHERE email=?", (employer.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(employer.password)

    cursor.execute(
        "INSERT INTO employer (name, company_name, email, phone, password) VALUES (?, ?, ?, ?, ?)",
        (employer.name, employer.company_name, employer.email, employer.phone, hashed_password),
    )
    conn.commit()
   