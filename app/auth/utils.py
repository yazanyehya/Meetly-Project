import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


ouat2_schema = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_token(token:str = Depends(ouat2_schema)):
    print("Incoming token:", token)
    print("Token expiry:", datetime.fromtimestamp(1739236419))
    print("Current time:", datetime.utcnow())

    try :
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        
        email:str =payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "Invalid token")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)