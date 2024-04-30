from fastapi import FastAPI, HTTPException,Query, Depends
import jwt
from jwt import PyJWTError, decode
from database import get_db_connection
# Secret key for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
conn = get_db_connection()
cursor = conn.cursor()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
from jwt import PyJWTError, decode
from pydantic import ValidationError
def get_current_emp_seeker_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        emp_id: int = int(payload.get("sub"))
        cursor.execute("SELECT * FROM employer WHERE employer_id=?", (emp_id,))
        user = cursor.fetchone()
        return user
    
    except (PyJWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials, please log in again"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail= "Token has expired")
    except (jwt.PyJWTError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail= "Invalid token")

    