import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.auth.models import User, SlotTime, Meeting
from app.auth.utils import hash_password, verify_password, verify_token

# Load environment variables from the .env file
load_dotenv()

router = APIRouter()

# Load sensitive configurations from .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define the request models
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role:str = "student"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class SlotRequest(BaseModel):
    start: datetime
    end: datetime

class BookSlotRequest(BaseModel):
    slot_id: int
    meeting_purpose:str
    

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_logged_in_user(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    print(f"Authorization header received: {token}")
    if not token:
        print("Authorization header is missing")
        raise HTTPException(status_code=401, detail="Authorization token missing")
    
    if not token.startswith("Bearer "):
        print("Token does not start with 'Bearer'")
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = token.replace("Bearer ", "")
    print(f"Token after removing 'Bearer': {token}")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")
        user_id = payload.get("sub")
        if not user_id:
            print("User ID not found in token payload")
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"No user found for ID: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError as e:
        print(f"JWT error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Check if the email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(data.password)
    # Create a new user
    new_user = User(
        name=data.name,
        email=data.email,
        password=hashed_password,
        role=data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    decoded_token = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])

    print("Decoded token:", decoded_token)


    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
    }

@router.post("/create_slot")
def create_slot(data: SlotRequest, request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if user.role != "professor":
        raise HTTPException(status_code=403, detail="Only professors can create slots")

    new_slot = SlotTime(
        professor_id=user.id,
        start_time=data.start,
        end_time=data.end,
        is_booked=False
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return {"message": "Slot created successfully", "slot_id": new_slot.id}

@router.get("/get_slots",dependencies=[Depends(verify_token)])
def get_slots(request:Request ,db: Session = Depends(get_db)):
    user = get_logged_in_user(request,db)
    if user.role not in ["student", "professor"]:
        raise HTTPException(status_code=403, detail="Access denied")
    slots = db.query(SlotTime).filter(SlotTime.is_booked == False).all()
    return [
        {
            "id": slot.id,
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "professor_id": slot.professor_id,
            "is_booked": slot.is_booked,
        }
        for slot in slots
    ]

@router.post("/book_slot")
def book_slot(data: BookSlotRequest, request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can book slots")

    slot = db.query(SlotTime).filter(SlotTime.id == data.slot_id, SlotTime.is_booked == False).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found or already booked")

    slot.is_booked = True
    db.commit()
    
    new_meeting = Meeting(
        slot_id=slot.id,
        student_id=user.id,
        professor_id=slot.professor_id,
        meeting_details=data.meeting_purpose
        
    )
    db.add(new_meeting)
    db.commit()

    return {"message": "Slot booked successfully", "meeting_id": new_meeting.id}


@router.post("/promote_to_professor")
def promote_to_professor(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "professor" :
        raise HTTPException(status_code = 400,detail="user is already a professor")
    user.role = "professor"
    db.commit()
    
    return {"message": f"{user.name} has been promoted to professor"}


@router.get("/calendar", dependencies=[Depends(verify_token)])
def get_calendar(request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    if user.role not in ["student", "professor"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"message": "Welcome to the calendar page!"}
