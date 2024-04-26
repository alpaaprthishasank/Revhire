from pydantic import BaseModel, EmailStr

class Job(BaseModel):
    title: str
    description: str
    salary: float
    location: str

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
