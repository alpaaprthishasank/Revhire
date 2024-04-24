from fastapi import FastAPI, HTTPException,Query, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import sqlite3
import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import date
from fastapi import HTTPException
from jwt import PyJWTError, decode
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from job_operations import update_job_details
from search import search_jobs
class Job(BaseModel):
    title: str
    description: str
    salary: float
    location: str

app = FastAPI()

# Database file
db_file = 'job_portal.db'

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Secret key for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# Define models for FastAPI
class JobSeeker(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

class Employer(BaseModel):
    name: str
    company_name: str
    email: EmailStr
    phone: str
    password: str

class Application(BaseModel):
    job_id: int
    seeker_id: int

class JobUpdate(BaseModel):
    description: str
    salary: float
    location: str

# Function to create a database connection
def get_db_connection():
    conn = sqlite3.connect(db_file)
    return conn

# Function to initialize database tables
def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create job_seeker and employer tables if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_seeker (
            seeker_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employer (
            employer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            company_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS application (
            application_id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL,
            seeker_id INTEGER NOT NULL,
            employer_id INTEGER NOT NULL,
            application_date DATE NOT NULL DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (job_id) REFERENCES job (job_id),
            FOREIGN KEY (seeker_id) REFERENCES job_seeker (seeker_id),
            FOREIGN KEY (employer_id) REFERENCES employer (employer_id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database tables
initialize_db()

# Authentication functions
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

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Route to authenticate and get JWT token
@app.post("/login")
async def login(user_type: str, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password, user_type)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Generate JWT token
    user_id = user[0]
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Route to create a new job seeker
@app.post("/job_seeker/")
async def create_job_seeker(job_seeker: JobSeeker):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM job_seeker WHERE email=?", (job_seeker.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(job_seeker.password)

    cursor.execute(
        "INSERT INTO job_seeker (name, email, phone, password) VALUES (?, ?, ?, ?)",
        (job_seeker.name, job_seeker.email, job_seeker.phone, hashed_password),
    )
    conn.commit()
    conn.close()

    return {"message": "Job seeker created successfully"}

# Route to create a new employer
@app.post("/employer/")
async def create_employer(employer: Employer):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employer WHERE email=?", (employer.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(employer.password)

    cursor.execute(
        "INSERT INTO employer (name, company_name, email, phone, password) VALUES (?, ?, ?, ?, ?)",
        (employer.name, employer.company_name, employer.email, employer.phone, hashed_password),
    )
    conn.commit()
    conn.close()

    return {"message": "Employer created successfully"}

# Protected route example for job seekers
@app.get("/protected_job_seeker/")
async def protected_job_seeker_route(token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify the access_token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])  # Extract user_id from the token's payload

        # Retrieve user information from the database based on user_id
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM job_seeker WHERE seeker_id=?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Return user information or perform other actions based on authentication
        return {"user_id": user_id, "username": user[1]}  # Assuming username is the second column (index 1)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.JWTError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")

# Protected route example for employers
@app.get("/protected_employer/")
async def protected_employer_route(token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify the access_token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])  # Extract user_id from the token's payload

        # Retrieve user information from the database based on user_id
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employer WHERE employer_id=?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Return user information or perform other actions based on authentication
        return {"user_id": user_id, "username": user[1]}  # Assuming username is the second column (index 1)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (jwt.JWTError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/jobs/")
async def create_job(job: Job, token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify the access_token to get the employer_id
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        employer_id = int(payload["sub"])  # Extract employer_id from the token's payload

        # Create a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the employer exists
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
    except (jwt.JWTError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail="Invalid token")


# Route to retrieve all job seekers
@app.get("/job_seekers/")
async def get_job_seekers():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT seeker_id, name, email,password ,phone FROM job_seeker")
    job_seekers = cursor.fetchall()

    conn.close()
    return {"job_seekers": job_seekers}

# Route to retrieve all employers
@app.get("/employers/")
async def get_employers():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT employer_id, name, company_name, email,password, phone FROM employer")
    employers = cursor.fetchall()

    conn.close()
    return {"employers": employers}
@app.get("/jobs/")
async def get_jobs():
    try:
        # Create a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve all jobs from the database
        cursor.execute("SELECT * FROM job")
        jobs = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Return the list of jobs as a response
        return {"jobs": jobs}

    except Exception as e:
        # Handle any database errors or exceptions
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


def get_current_job_seeker_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        job_seeker_id: int = int(payload.get("sub"))
        return job_seeker_id
    except (PyJWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials, please log in again"
        )

@app.post("/apply_job/")
async def apply_job(
    job_id: int,
    current_job_seeker_id: int = Depends(get_current_job_seeker_id)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve employer_id associated with the job_id
    cursor.execute("SELECT employer_id FROM job WHERE job_id=?", (job_id,))
    job_data = cursor.fetchone()

    if not job_data:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")

    employer_id = job_data[0]

    # Insert the job application into the application table
    cursor.execute(
        "INSERT INTO application (job_id, seeker_id, employer_id, application_date) VALUES (?, ?, ?, ?)",
        (job_id, current_job_seeker_id, employer_id, datetime.today())
    )
    conn.commit()
    conn.close()

    return {"message": "Job application submitted successfully"}



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)


@app.get('/jobs/search', response_model=list[Job])
async def search_jobs_endpoint(keyword: str = Query(..., min_length=1)):
    try:
        jobs = await search_jobs(keyword)
        if not jobs:
            raise HTTPException(status_code=404, detail="No jobs found matching the search criteria")
        return jobs
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@app.put('/jobs/{job_id}', response_model=JobUpdate)
async def update_job(job_id: int, job_update: JobUpdate, employer_id: int = Depends(get_current_job_seeker_id)):
    # Validate employer_id and perform authorization logic here if needed

    # Call the update_job_details function from job_operations.py
    update_job_details(job_id, job_update.dict())

    return job_update



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)

