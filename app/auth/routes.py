import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.auth.models import User, SlotTime, Meeting,WaitList,PreferredTime,Notification,RescheduleRequest
from app.auth.utils import hash_password, verify_password, verify_token,build_matching_graph,send_notification,max_bipartite_matching,get_user_assignments

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
    
class RescheduleResponse(BaseModel):
    reschedule_id: int
    response: str

class WaitListRequest(BaseModel):
    slot_id: int

    
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
        "user_id": user.id

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
    slots = db.query(SlotTime).all()
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

@router.get("/student/meetings")
def get_student_meetings(request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    print(f"Logged-in user: {user.id}")  # Debugging

    
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view their meetings")

    meetings = db.query(Meeting).filter(Meeting.student_id == user.id).all()
    print(f"Meetings found: {meetings}")  # Debugging


    return [
        {
            "id": meeting.id,
            "meeting_purpose": meeting.meeting_details,
            "start_time": meeting.slot.start_time.isoformat(),
            "end_time": meeting.slot.end_time.isoformat(),
            "professor_name": meeting.professor.name if meeting.professor else "Unknown",
        }
        for meeting in meetings
    ]

@router.delete("/student/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.student_id == user.id
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    slot = db.query(SlotTime).filter(SlotTime.id == meeting.slot_id).first()
    if slot:
        # Free the slot
        slot.is_booked = False

    # Delete the meeting
    db.delete(meeting)
    db.commit()

    # Check if there's anyone on the waitlist
    waitlist_entry = (
        db.query(WaitList)
        .filter(WaitList.slot_id == slot.id)
        .order_by(WaitList.created_at.asc())  # earliest user first
        .first()
    )

    if waitlist_entry:
        # Book the slot for that user
        new_meeting = Meeting(
            slot_id=slot.id,
            student_id=waitlist_entry.user_id,
            professor_id=slot.professor_id,
            meeting_details="(Auto-booked from waitlist)",
        )
        db.add(new_meeting)
        slot.is_booked = True  # slot is now booked again

        # Remove them from waitlist
        db.delete(waitlist_entry)

        db.commit()

    return {"message": "Meeting deleted successfully"}



@router.get("/get_slots_by_date", dependencies=[Depends(verify_token)])
def get_slots_by_date(request: Request, date: str, db: Session = Depends(get_db)):
    user = get_logged_in_user(request, db)

    slots = db.query(SlotTime).filter(SlotTime.start_time.startswith(date)).all()

    return [
        {
            "id": slot.id,
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "is_booked": slot.is_booked,
        }
        for slot in slots
    ]

@router.post("/add_to_waitlist")
def add_to_waitlist(
    data: WaitListRequest, 
    request: Request, 
    db: Session = Depends(get_db)
):
    slot_id = data.slot_id
    # 1. Validate user
    user = get_logged_in_user(request, db)
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can join waitlist")

    # Extract slot_id from the request body
    slot_id = data.slot_id

    # 2. Check if slot exists & is currently booked
    slot = db.query(SlotTime).filter(SlotTime.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if not slot.is_booked:
        raise HTTPException(status_code=400, detail="Slot is free; you can book it directly")

    existing_meeting = db.query(Meeting).filter(Meeting.slot_id == slot_id).first()
    if not existing_meeting:
        raise HTTPException(status_code=400, detail="No active meeting found for this slot")

    # ---------------------------
    # Attempt bipartite matching
    # ---------------------------
    print("🚀 Building matching graph...")
    user_to_slots, slot_to_user = build_matching_graph(db)
    print(f"user_to_slots = {user_to_slots}")
    print(f"slot_to_user = {slot_to_user}")

    before = sum(1 for x in slot_to_user.values() if x is not None)
    max_bipartite_matching(user_to_slots, slot_to_user)
    after = sum(1 for x in slot_to_user.values() if x is not None)
    print(f"Match count before = {before}, after = {after}")

    final_assignments = get_user_assignments(slot_to_user)
    print(f"Final user assignments = {final_assignments}")

    # Check if this user got a slot via the new matching
    if user.id in final_assignments:
        new_slot_id = final_assignments[user.id]

        if new_slot_id != slot_id:
            print(f"✅ Found a potential move: occupant can go from {slot_id} to {new_slot_id} so user {user.id} can have {slot_id}.")
            
            # Identify the occupant who currently holds slot_id
            occupant_id = slot_to_user[slot_id]
            if occupant_id is None:
                # If it's None, that means we are not actually displacing anyone.
                # But the BFS said we are. This can happen if the occupant was re-matched
                # to something else. If occupant_id is None, just do direct assignment
                pass
            else:
                # occupant_id is the user who is currently in slot_id and must be moved
                # Grab occupant's meeting
                occupant_meeting = db.query(Meeting).filter(
                    Meeting.student_id == occupant_id,
                    Meeting.slot_id == slot_id
                ).first()

                if occupant_meeting:
                    # Create a pending reschedule request
                    res_req = RescheduleRequest(
                        user_id=occupant_id,          # occupant who must move
                        current_slot_id=slot_id,
                        new_slot_id=new_slot_id,
                        professor_id=occupant_meeting.professor_id,
                        status="Pending"
                    )
                    db.add(res_req)
                    db.commit()
                    
                    # Notify occupant
                    send_notification(
                        occupant_id,
                        f"You have a request to move from slot {slot_id} to slot {new_slot_id} so user {user.id} can take slot {slot_id}.",
                        db
                    )

            # The new user (user.id) still doesn't have the slot yet,
            # so put them on waitlist until occupant accepts.
            waitlist_entry = WaitList(slot_id=slot_id, user_id=user.id)
            db.add(waitlist_entry)
            db.commit()

            return {"message": f"Requested occupant {occupant_id} to move. You have been added to the waitlist."}


    

@router.get("/users/{user_id}/preferences")
def get_preference(user_id:int, db:Session=Depends(get_db)):
    user = db.query(User).filter(User.id==user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs =[]
    for p in user.preferred_times:
        time_str = p.time_slot.strftime("%Y-%m-%dT%H:%M")
        prefs.append(time_str)

    return {"user_id": user_id, "preferred_times": prefs}

    

# Create a notification
@router.post("/notifications")
def create_notification(user_id: int, message: str, db: Session = Depends(get_db)):
    notification = Notification(user_id=user_id, message=message)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return {"message": "Notification created successfully", "notification": notification}

# Get all unread notifications for a user
@router.get("/notifications")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id, Notification.is_read == False
    ).order_by(Notification.created_at.desc()).all()
    
    return {"notifications": notifications}

# Mark a notification as read
@router.post("/notifications/mark_as_read")
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}

@router.post("/reschedule_requests/{request_id}/accept")
def accept_reschedule_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Occupant calls this to accept the move from their current slot to the new slot.
    """

    # 1. Find the RescheduleRequest
    res_req = db.query(RescheduleRequest).filter(RescheduleRequest.id == request_id).first()
    if not res_req:
        raise HTTPException(status_code=404, detail="No such reschedule request found.")

    # 2. Check if this request is still pending
    if res_req.status != "Pending":
        raise HTTPException(status_code=400, detail="Reschedule request is not pending.")

    # 3. Confirm the current user is the occupant who needs to move
    user = get_logged_in_user(request, db)
    if user.id != res_req.user_id:
        raise HTTPException(status_code=403, detail="You are not the occupant for this request.")

    # 4. Mark the request as Accepted
    res_req.status = "Accepted"
    db.commit()

    # 5. Finalize the move in the database
    finalize_reschedule_move(res_req, db)

    return {"message": f"Reschedule request {request_id} accepted and finalized."}

@router.post("/reschedule_requests/{request_id}/reject")
def reject_reschedule_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Occupant calls this to reject the move.
    """
    res_req = db.query(RescheduleRequest).filter(RescheduleRequest.id == request_id).first()
    if not res_req:
        raise HTTPException(status_code=404, detail="No such reschedule request found.")

    if res_req.status != "Pending":
        raise HTTPException(status_code=400, detail="Reschedule request is not pending.")

    user = get_logged_in_user(request, db)
    if user.id != res_req.user_id:
        raise HTTPException(status_code=403, detail="You are not the occupant for this request.")

    # Mark it as Rejected
    res_req.status = "Rejected"
    db.commit()

    # Optionally notify the user who wanted the slot that occupant refused
    return {"message": f"Reschedule request {request_id} rejected. No changes made."}


def finalize_reschedule_move(res_req: RescheduleRequest, db: Session):
    """
    Actually move the occupant from res_req.current_slot_id to res_req.new_slot_id,
    free the old slot, and assign that old slot to whoever was waiting (the new user).
    """

    # 1. Free occupant's old slot
    old_slot = db.query(SlotTime).filter(SlotTime.id == res_req.current_slot_id).first()
    if old_slot:
        old_slot.is_booked = False

    # 2. Mark occupant's new slot as booked
    new_slot = db.query(SlotTime).filter(SlotTime.id == res_req.new_slot_id).first()
    if new_slot:
        new_slot.is_booked = True

    # 3. Update occupant's Meeting from the old slot to the new slot
    occupant_meeting = db.query(Meeting).filter(
        Meeting.student_id == res_req.user_id,
        Meeting.slot_id == res_req.current_slot_id
    ).first()

    if occupant_meeting:
        occupant_meeting.slot_id = res_req.new_slot_id

    # 4. Now that old_slot is freed, give it to the user who originally
    #    requested it. Easiest approach is to see if there's a WaitList
    #    entry for old_slot (the user who triggered this chain).
    #    We'll just take the earliest from the waitlist for that slot.
    waitlist_entry = db.query(WaitList).filter(WaitList.slot_id == res_req.current_slot_id)\
        .order_by(WaitList.created_at.asc())\
        .first()

    if waitlist_entry:
        # book the slot for that user
        new_meeting = Meeting(
            slot_id=res_req.current_slot_id,
            student_id=waitlist_entry.user_id,
            professor_id=old_slot.professor_id if old_slot else res_req.professor_id,
            meeting_details="(Reschedule auto-booked)"
        )
        db.add(new_meeting)
        # mark the old slot as re-booked
        if old_slot:
            old_slot.is_booked = True

        # remove them from waitlist
        db.delete(waitlist_entry)

    # 5. Mark the request as Finalized
    res_req.status = "Finalized"
    db.commit()
