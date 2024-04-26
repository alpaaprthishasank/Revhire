from fastapi import FastAPI, HTTPException,Query, Depends
import jwt
# Secret key for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
from jwt import PyJWTError, decode
from pydantic import ValidationError
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