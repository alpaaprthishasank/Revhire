from fastapi import HTTPException, Depends
from datetime import date
from models import Job
import jwt
import sqlite3
from jwt import PyJWTError, decode

from database import get_db_connection
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

conn = get_db_connection()
cursor = conn.cursor()
def post_job(token: str, job: Job):
    try:
        print(token)
        print(job)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employer_id = int(payload["sub"])
        cursor.execute("SELECT * FROM employer WHERE employer_id=?", (employer_id,))
        employer = cursor.fetchone()
        if not employer:
            conn.close()
            raise HTTPException(status_code=404, detail="Employer not found")

        # Insert the job into the database
        cursor.execute(
            "INSERT INTO job (employer_id, title, description, salary, location, posted_date) VALUES (?, ?, ?, ?, ?, ?)",
            (employer_id, job.title, job.description, job.salary, job.location, date.today()),
        )
        conn.commit()
        conn.close()

        return {"message": "Job posted successfully"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.PyJWTError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")
