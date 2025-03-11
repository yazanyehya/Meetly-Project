import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime
from app.auth.models import PreferredTime,SlotTime,Meeting,Notification,User
from sqlalchemy.orm import Session


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


def build_matching_graph(db: Session):
    """
    Build a bipartite graph mapping:
      - user_to_slots[user_id] = list of slot_ids the user *could* use (based on preferences).
      - slot_to_user[slot_id] = occupant_user_id if booked, or None if free.

    Returns (user_to_slots, slot_to_user).
    """

    # 1. Initialize the adjacency dict for all *students*
    user_to_slots = {}  # { user_id: [slot_id, slot_id, ...] }
    all_students = db.query(User).filter(User.role == "student").all()
    for student in all_students:
        user_to_slots[student.id] = []

    # 2. Populate user_to_slots from PreferredTime
    #    For each PreferredTime, find a SlotTime with the same start_time
    preferred_rows = db.query(PreferredTime).all()
    for pref in preferred_rows:
        user_id = pref.user_id
        # Make sure this user is in user_to_slots (they might have no other preferences yet)
        if user_id not in user_to_slots:
            user_to_slots[user_id] = []

        matching_slot = db.query(SlotTime).filter(SlotTime.start_time == pref.time_slot).first()
        if matching_slot:
            if matching_slot.id not in user_to_slots[user_id]:
                user_to_slots[user_id].append(matching_slot.id)

    # 3. Build slot_to_user from existing meetings
    slot_to_user = {}  # { slot_id: occupant_user_id or None }
    all_slots = db.query(SlotTime).all()
    for slot in all_slots:
        slot_to_user[slot.id] = None  # default to free

    # 4. Fill occupant info for booked slots
    booked_meetings = db.query(Meeting).all()
    for meeting in booked_meetings:
        slot_id = meeting.slot_id
        student_id = meeting.student_id
        # Mark who is occupying that slot
        slot_to_user[slot_id] = student_id

    return user_to_slots, slot_to_user

def _find_augmenting_path(user_id, user_to_slots, slot_to_user, visited):
    """
    DFS-like method to find an augmenting path for user_id.

    user_id: the user we are trying to match
    user_to_slots: dict => user_id -> [slot_id, slot_id, ...]
    slot_to_user: dict => slot_id -> occupant_user_id or None
    visited: set of slot_ids visited in this DFS iteration
    """
    for slot_id in user_to_slots[user_id]:
        # If we haven't visited this slot yet in this DFS:
        if slot_id not in visited:
            visited.add(slot_id)  # Mark the slot as visited

            occupant = slot_to_user[slot_id]  # who is currently in this slot (None if free)
            # If slot is free OR we can find another slot for the occupant
            if occupant is None or _find_augmenting_path(occupant, user_to_slots, slot_to_user, visited):
                slot_to_user[slot_id] = user_id  # Assign slot to this user
                return True

    return False


def max_bipartite_matching(user_to_slots, slot_to_user):
    """
    Runs a bipartite matching using DFS to find augmenting paths.
    Updates slot_to_user in place.

    Returns an integer: how many total matches (i.e., how many users got a slot).
    """

    match_count = 0
    # For each user, try to find an available slot (or reshuffle)
    for user_id in user_to_slots:
        visited = set()  # Track visited slots each time we attempt to match user_id
        if _find_augmenting_path(user_id, user_to_slots, slot_to_user, visited):
            match_count += 1

    return match_count


def get_user_assignments(slot_to_user):
    """
    Invert the final slot_to_user mapping into a user->slot dict
    so we can quickly see which slot a given user ended up with.
    """
    user_assignment = {}
    for slot_id, occupant in slot_to_user.items():
        if occupant is not None:
            user_assignment[occupant] = slot_id
    return user_assignment







def send_notification(user_id, message, db):
    """
    Stores notifications in the database and prints to console.
    """
    notification = Notification(user_id=user_id, message=message)
    db.add(notification)
    db.commit()
    print(f"✅ Notification saved for User {user_id}: {message}")



