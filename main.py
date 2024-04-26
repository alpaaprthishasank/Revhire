from fastapi import FastAPI, HTTPException,Query, Depends, Response, Header
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
from job_sekker import create_job_seeker_in_db
from database import get_db_connection
from create_token import create_access_token
from Auth import authenticate_user
from current_job_seeker_id import get_current_job_seeker_id
from models import Job,JobSeeker,JobUpdate,Application,Employer
from create_employer import create_employer_in_db
import prometheus_client
import logging
from prometheus_client.core import CollectorRegistry
from prometheus_client import Counter,Histogram,Summary

app = FastAPI()
logging.basicConfig(filename="users.log",encoding='utf-8',filemode='a',level=logging.INFO)
logger=logging.getLogger(__name__)
import time
graphs={}

graphs['job_seeker_reg_counter']=Counter('job_seeker_counter','this is job_seeker reg page')
graphs['emp_reg_counter']=Counter('emp_counter','this is emp reg page')
graphs['login_page_counter']=Counter('login_counter','this is login page')
graphs['jobs_counter']=Counter('job_counter','this is jobs  page')
graphs['apply_job_counter']=Counter('apply_job_counter','this is apply job page')


graphs['job_seeker_reg_hist']=Histogram('job_seeker_hist','get hey python',buckets={1,2,3,5,7,float('inf')})
graphs['emp_reg_hist']=Histogram('home_hist','get home page',buckets={1,2,3,5,7,float('inf')})
graphs['login_page_hist']=Histogram('login_page_hist','counter for get users',buckets={1,2,3,5,7,float('inf')})
graphs['jobs_hist'] = Histogram('jobs_hist','get_users_duration_seconds',buckets={1,2,3,5,7,float('inf')})
graphs['apply_job_hist']=Histogram('apply_job_hist','this is apply job page',buckets={1,2,3,5,7,float('inf')})

@app.get("/metrics")
def metrics():
    result=[]
    for k,v in graphs.items():
        result.append(prometheus_client.generate_latest(v))
    return result
@app.get("/")
def startpage():
    return "hi this start project0"
# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Secret key for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
conn = get_db_connection()
cursor = conn.cursor()
#routes
@app.post("/login")
async def login(user_type: str, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password, user_type)
    start=time.time()
    graphs['login_page_counter'].inc()
    graphs['login_page_hist'].observe(time.time()-start)
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
    start=time.time()
    graphs['job_seeker_reg_counter'].inc()
    graphs['job_seeker_reg_hist'].observe(time.time()-start)
    create_job_seeker_in_db(cursor, conn, job_seeker)
    conn.close()
    return {"message": "Job seeker created successfully"}

# Route to create a new employer
@app.post("/employer/")
async def create_employer(employer: Employer):
    start=time.time()
    graphs['emp_reg_counter'].inc()
    graphs['emp_reg_hist'].observe(time.time()-start)
    create_employer_in_db(employer)
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
        raise HTTPException(status_code=401, detail= "Token has expired")
    except (jwt.JWTError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail= "Invalid token")

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
    finally:
        start=time.time()
        graphs['jobs_counter'].inc()
        graphs['jobs_hist'].observe(time.time()-start)


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



@app.post("/apply_job/")
async def apply_job(
    job_id: int,
    current_job_seeker_id: int = Depends(get_current_job_seeker_id)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    start=time.time()
    graphs['apply_job_counter'].inc()
    graphs['apply_job_hist'].observe(time.time()-start)
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




