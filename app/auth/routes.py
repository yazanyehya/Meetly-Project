import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.auth.models import User, SlotTime, Meeting,WaitList,PreferredTime,Notification,RescheduleRequest
from app.auth.utils import hash_password, verify_password, verify_token,build_matching_graph,send_notification,max_bipartite_matching,get_user_assignments,visualize_matching_graph,try_single_user_bfs_in_memory

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

class PreferenceRequest(BaseModel):
    time_slots: list[str]
    
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
        slot.is_booked = False

    db.delete(meeting)
    db.commit()

    # 1) See if a user is on waitlist for THIS slot. If so, assign them directly:
    waitlist_entry = db.query(WaitList).filter(
        WaitList.slot_id == slot.id
    ).order_by(WaitList.created_at.asc()).first()

    if waitlist_entry:
        slot.is_booked = True
        new_meeting = Meeting(
            slot_id=slot.id,
            student_id=waitlist_entry.user_id,
            professor_id=slot.professor_id,
            meeting_details="(Auto-booked from waitlist)"
        )
        db.add(new_meeting)
        db.delete(waitlist_entry)
        db.commit()
        return {"message": f"Meeting deleted. Slot {slot.id} assigned to waitlisted user {waitlist_entry.user_id}"}

    # 2) Otherwise, loop over the entire waitlist to see if we can seat someone via BFS
    all_waitlist = db.query(WaitList).order_by(WaitList.created_at.asc()).all()
    if not all_waitlist:
        return {"message": "Meeting deleted. No waitlisted user needed that slot."}

    for wl in all_waitlist:
        waitlisted_user_id = wl.user_id

        # BFS in memory
        slot_to_user_new = try_single_user_bfs_in_memory(waitlisted_user_id, db)
        if slot_to_user_new is None:
            # can't seat this user, check next
            continue

        # 3) BFS succeeded. Figure out occupant chain for the new occupant mapping
        from copy import deepcopy

        # Rebuild old occupant assignment
        user_to_slots, original_slot_to_user = build_matching_graph(db)
        old_assignments = {}
        for sid, occupant in original_slot_to_user.items():
            if occupant is not None:
                old_assignments[occupant] = sid

        # Build new occupant assignment
        final_assignments = {}
        for sid, occupant in slot_to_user_new.items():
            if occupant is not None:
                final_assignments[occupant] = sid

        # 4) Identify the chain of users who actually changed slots
        #    We'll replicate your "move_chain" approach from add_to_waitlist
        move_chain = []
        checked_users = set()
        current_user = waitlisted_user_id

        while current_user in final_assignments and current_user not in checked_users:
            next_slot_id = final_assignments[current_user]
            occupant_meeting = db.query(Meeting).filter(
                Meeting.slot_id == next_slot_id
            ).first()

            if not occupant_meeting:
                break

            move_chain.append((
                occupant_meeting.student_id,
                occupant_meeting.slot_id,
                next_slot_id,
                occupant_meeting.professor_id
            ))
            checked_users.add(current_user)
            current_user = occupant_meeting.student_id

        # filter out the new waitlisted user from the occupant chain
        affected_users = [
            user_id for (user_id, _, _, _) in move_chain
            if user_id != waitlisted_user_id
        ]
        correct_new_slots = {
            u_id: final_assignments[u_id]
            for u_id in affected_users
        }

        if move_chain and affected_users:
            # 5) Create or find a RescheduleRequest
            from app.auth.models import RescheduleRequest

            existing_request = db.query(RescheduleRequest).filter(
                RescheduleRequest.user_ids == ",".join(str(u) for u in affected_users),
                RescheduleRequest.current_slot_ids == ",".join(str(s) for _, s, _, _ in move_chain),
                RescheduleRequest.new_slot_ids == ",".join(str(correct_new_slots[u]) for u in affected_users)
            ).first()

            if not existing_request:
                res_req = RescheduleRequest(
                    user_ids=",".join(str(u) for u in affected_users),
                    current_slot_ids=",".join(str(s) for _, s, _, _ in move_chain),
                    new_slot_ids=",".join(str(correct_new_slots[u]) for u in affected_users),
                    professor_ids=",".join(str(p) for _, _, _, p in move_chain),
                    status="Pending"
                )
                db.add(res_req)
                db.commit()

                # send notifications to each occupant
                for occupant_id in affected_users:
                    send_notification(
                        occupant_id,
                        f"You have a request to move to slot {correct_new_slots[occupant_id]} "
                        f"(Request ID: {res_req.id}).",
                        db,
                        reschedule_id=res_req.id
                    )

            # 6) The waitlisted user remains unmatched in the DB until acceptance, so keep them in WaitList
            return {
                "message": "Created reschedule request. Occupants must accept. No occupant changes applied yet."
            }

    # If we reach here, no BFS chain for any user
    return {"message": "Meeting deleted. No waitlisted user could be placed."}

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
    user = get_logged_in_user(request, db)
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can join waitlist")

    slot_id = data.slot_id

    # Check if slot exists & is booked
    slot = db.query(SlotTime).filter(SlotTime.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if not slot.is_booked:
        raise HTTPException(status_code=400, detail="Slot is free; you can book it directly")

    existing_meeting = db.query(Meeting).filter(Meeting.slot_id == slot_id).first()
    if not existing_meeting:
        raise HTTPException(status_code=400, detail="No active meeting found for this slot")

    # 📊 Before Matching: Show initial graph
    user_to_slots, slot_to_user = build_matching_graph(db)
    visualize_matching_graph(user_to_slots, slot_to_user, title="Before Matching")

    # 🔄 Perform bipartite matching
    before = sum(1 for x in slot_to_user.values() if x is not None)
    max_bipartite_matching(user_to_slots, slot_to_user)
    after = sum(1 for x in slot_to_user.values() if x is not None)
    final_assignments = get_user_assignments(slot_to_user)

    # 📊 After Matching: Show updated graph
    visualize_matching_graph(user_to_slots, slot_to_user, title="After Matching")

    # 🛑 If no rearrangement found, add to waitlist
    if user.id not in final_assignments:
        waitlist_entry = WaitList(slot_id=slot_id, user_id=user.id)
        db.add(waitlist_entry)
        db.commit()
        return {"message": "No available rearrangements. You have been added to the waitlist."}

    # 🚀 Identify users who ACTUALLY need to move (exclude the waitlisted user)
    move_chain = []
    checked_users = set()
    current_user = user.id

    while current_user in final_assignments and current_user not in checked_users:
        next_slot = final_assignments[current_user]
        occupant_meeting = db.query(Meeting).filter(Meeting.slot_id == next_slot).first()

        if not occupant_meeting:
            break  # No further user to move

        move_chain.append((occupant_meeting.student_id, occupant_meeting.slot_id, next_slot, occupant_meeting.professor_id))
        checked_users.add(current_user)
        current_user = occupant_meeting.student_id

    # ✅ Filter only affected users (EXCLUDE the original requester)
    affected_users = [user_id for user_id, _, _, _ in move_chain if user_id != user.id]

    # ✅ Ensure correct new slot assignments
    correct_new_slots = {user_id: final_assignments[user_id] for user_id in affected_users}

    # 🚀 Debugging
    print(f"DEBUG: Move Chain = {move_chain}")
    print(f"DEBUG: Affected Users = {affected_users}")
    print(f"DEBUG: Correct New Slots = {correct_new_slots}")

    # 🔥 If multiple users need to move, we need approvals from all
    if move_chain and affected_users:
        existing_request = db.query(RescheduleRequest).filter(
            RescheduleRequest.user_ids == ",".join(str(user_id) for user_id in affected_users),
            RescheduleRequest.current_slot_ids == ",".join(str(current_slot) for _, current_slot, _, _ in move_chain),
            RescheduleRequest.new_slot_ids == ",".join(str(correct_new_slots[user_id]) for user_id in affected_users),
        ).first()

        if not existing_request:  # ✅ Prevent duplicate insertions
            reschedule_request = RescheduleRequest(
                user_ids=",".join(str(user_id) for user_id in affected_users),
                current_slot_ids=",".join(str(current_slot) for _, current_slot, _, _ in move_chain),
                new_slot_ids=",".join(str(correct_new_slots[user_id]) for user_id in affected_users),
                professor_ids=",".join(str(prof_id) for _, _, _, prof_id in move_chain),
                status="Pending"
            )
            db.add(reschedule_request)
            db.commit()

            # 🔔 Send notifications to all affected users
            for user_id in affected_users:
                send_notification(
                    user_id,
                    f"You have a request to move to slot {correct_new_slots[user_id]} (Request ID: {reschedule_request.id}).",
                    db,
                    reschedule_id=reschedule_request.id  # Pass the reschedule request ID
                )

        # ✅ User is waitlisted until all moves are accepted
        waitlist_entry = WaitList(slot_id=slot_id, user_id=user.id)
        db.add(waitlist_entry)
        db.commit()

        return {
            "message": f"Notified {len(affected_users)} users. User {user.id} is waitlisted until all approve."
        }

    return {"message": "Unexpected error in waitlist process."}


@router.get("/users/{user_id}/preferences")
def get_preference(user_id:int, db:Session=Depends(get_db)):
    user = db.query(User).filter(User.id==user_id).first()
    print(user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    prefs =[]
    for p in user.preferred_times:
        time_str = p.time_slot.strftime("%Y-%m-%dT%H:%M")
        prefs.append(time_str)

    return {
        "user_id": user_id,
        "preferred_times": [
            {"id": p.id, "time_slot": p.time_slot.strftime("%Y-%m-%dT%H:%M")}
            for p in user.preferred_times
        ]
    }

@router.post("/users/{user_id}/preferences")
def save_preference(user_id: int, data: PreferenceRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_times = {p.time_slot for p in db.query(PreferredTime).filter(PreferredTime.user_id == user_id).all()}

    new_times = set(datetime.fromisoformat(t) for t in data.time_slots)

    # ✅ Append new times instead of deleting everything
    for new_time in new_times - existing_times:
        db.add(PreferredTime(user_id=user_id, time_slot=new_time))

    db.commit()
    return {"message": "Preferences updated successfully"}


# Create a notification
@router.post("/notifications")
def create_notification(user_id: int, message: str, reschedule_id: int, db: Session = Depends(get_db)):
    notification = Notification(user_id=user_id, message=message, reschedule_id=reschedule_id)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return {"message": "Notification created successfully", "notification": notification}


@router.get("/notifications")
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).all()

    return [
        {
            "id": notification.id,
            "message": notification.message,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
            # ✅ Only include `reschedule_id` if it exists in the model
            **({"reschedule_id": notification.reschedule_id} if hasattr(notification, "reschedule_id") else {})
        }
        for notification in notifications
    ]


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
    If all users accept, finalize the reschedule.
    """

    # ✅ Debug: Print all request IDs before querying
    all_requests = db.query(RescheduleRequest).all()
    print(f"DEBUG: Available request IDs: {[r.id for r in all_requests]}")

    res_req = db.query(RescheduleRequest).filter(RescheduleRequest.id == request_id).first()
    
    # ✅ Fix: Ensure the request exists
    if not res_req:
        raise HTTPException(status_code=404, detail="No such reschedule request found.")

    # ✅ Debug: Print current request data
    print(f"DEBUG: Reschedule Request Found - ID: {res_req.id}, Users: {res_req.user_ids}, Status: {res_req.status}")

    # ✅ Ensure status is pending
    if res_req.status != "Pending":
        raise HTTPException(status_code=400, detail="Reschedule request is not pending.")

    user = get_logged_in_user(request, db)

    # ✅ Fix: Ensure `approved_user_ids` exists and is initialized
    if not hasattr(res_req, "approved_user_ids") or res_req.approved_user_ids is None:
        res_req.approved_user_ids = ""

    # ✅ Fix: Properly split and clean up spaces in `approved_user_ids`
    approved_users = [u.strip() for u in res_req.approved_user_ids.split(",") if u]
    approved_users.append(str(user.id))

    # ✅ Ensure uniqueness in approvals
    res_req.approved_user_ids = ",".join(set(approved_users))
    db.commit()

    # ✅ Debug: Show the updated approved users
    print(f"DEBUG: Updated approved_user_ids = {res_req.approved_user_ids}")

    # 🔄 Check if ALL required users have accepted
    required_users = [u.strip() for u in res_req.user_ids.split(",") if u]

    if set(approved_users) == set(required_users):
        finalize_reschedule_move(res_req, db)

        # ✅ Remove reschedule request after success
        db.delete(res_req)
        db.commit()

        # ✅ Notify the waiting user that their slot is now available
        waitlist_entry = db.query(WaitList).filter(WaitList.slot_id == res_req.current_slot_ids.split(",")[0]).first()
        if waitlist_entry:
            send_notification(
                waitlist_entry.user_id,
                "Your requested slot is now available!",
                db,
                reschedule_id=res_req.id  # Include reschedule ID
            )
            db.delete(waitlist_entry)
            db.commit()

        return {"message": f"Reschedule request {request_id} accepted and finalized."}

    return {"message": f"Reschedule request {request_id} partially approved. Waiting for others."}

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

    # After successful finalize, remove the reschedule request row altogether
    db.delete(res_req)
    db.commit()
    # Optionally notify the user who wanted the slot that occupant refused
    
    occupant_notification = db.query(Notification).filter(Notification.user_id == user.id)\
        .filter(Notification.message.ilike(f"%Request ID: {request_id}%"))\
        .first()

    if occupant_notification:
        db.delete(occupant_notification)
        db.commit()
    return {"message": f"Reschedule request {request_id} rejected. No changes made."}


def finalize_reschedule_move(res_req: RescheduleRequest, db: Session):
    """
    Actually move the occupant from res_req.current_slot_ids to res_req.new_slot_ids,
    free the old slot, and assign that old slot to whoever was waiting (the new user).
    """

    # ✅ Fix: Handle multiple slot IDs properly
    current_slot_ids = res_req.current_slot_ids.split(",")  # Convert string to list
    new_slot_ids = res_req.new_slot_ids.split(",")  # Convert string to list

    if not current_slot_ids or not new_slot_ids:
        raise HTTPException(status_code=400, detail="Invalid reschedule request data.")

    for current_slot_id, new_slot_id in zip(current_slot_ids, new_slot_ids):
        current_slot_id = int(current_slot_id.strip())  # Convert to integer
        new_slot_id = int(new_slot_id.strip())  # Convert to integer

        # 1. Free occupant's old slot
        old_slot = db.query(SlotTime).filter(SlotTime.id == current_slot_id).first()
        if old_slot:
            old_slot.is_booked = False

        # 2. Mark occupant's new slot as booked
        new_slot = db.query(SlotTime).filter(SlotTime.id == new_slot_id).first()
        if new_slot:
            new_slot.is_booked = True

        # 3. Update occupant's Meeting from the old slot to the new slot
        occupant_meeting = db.query(Meeting).filter(
            Meeting.slot_id == current_slot_id
        ).first()

        if occupant_meeting:
            occupant_meeting.slot_id = new_slot_id

        # 4. Now that old_slot is freed, assign it to the next waitlisted user
        waitlist_entry = db.query(WaitList).filter(WaitList.slot_id == current_slot_id)\
            .order_by(WaitList.created_at.asc()).first()

        if waitlist_entry:
            new_meeting = Meeting(
                slot_id=current_slot_id,
                student_id=waitlist_entry.user_id,
                professor_id=old_slot.professor_id if old_slot else res_req.professor_ids,
                meeting_details="(Reschedule auto-booked)"
            )
        
            db.add(new_meeting)
            if old_slot:
                old_slot.is_booked = True

            db.delete(waitlist_entry)

    # ✅ **Delete all notifications related to this reschedule request**
    db.query(Notification).filter(Notification.reschedule_id == res_req.id).delete()

    # 5. Mark the request as Finalized
    res_req.status = "Finalized"
    db.commit()
    

@router.delete("/users/{user_id}/preferences/{pref_id}")
def delete_preference(user_id: int, pref_id: int, db: Session = Depends(get_db)):
    pref = db.query(PreferredTime).filter(
        PreferredTime.id == pref_id,
        PreferredTime.user_id == user_id
    ).first()
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")
    db.delete(pref)
    db.commit()
    return {"message": "Preference deleted successfully"}
