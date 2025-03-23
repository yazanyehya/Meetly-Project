import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime
<<<<<<< HEAD
from sqlalchemy.orm import Session
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from collections import deque, defaultdict

from app.auth.models import (
    PreferredTime, SlotTime, Meeting, Notification, User, WaitList
)
=======
from app.auth.models import PreferredTime,SlotTime,Meeting,Notification,User
from sqlalchemy.orm import Session

>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

ouat2_schema = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_token(token: str = Depends(ouat2_schema)):
    print("Incoming token:", token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        if exp:
            print("Token expiry:", datetime.fromtimestamp(exp))
        else:
            print("No expiration found in token payload")
        print("Current time:", datetime.utcnow())

        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired")
    except jwt.PyJWTError as e:
        print("JWT error:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


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
<<<<<<< HEAD
def _find_augmenting_path(user_id, user_to_slots, slot_to_user, visited):
    """
    DFS-like method to find an augmenting path for user_id.
    This function now properly swaps users to free up slots.
    """

    for slot_id in user_to_slots.get(user_id, []):
        if slot_id in visited:
            continue

        visited.add(slot_id)
        occupant = slot_to_user.get(slot_id, None)  # Ensure occupant is properly assigned

        # If the slot is free, assign it to the user immediately
        if occupant is None:
            # ✅ Free the previous slot
            for prev_slot, prev_user in slot_to_user.items():
                if prev_user == user_id:
                    print(f"🔄 User {user_id} moves from Slot {prev_slot} to Slot {slot_id}")
                    slot_to_user[prev_slot] = None  # Free old slot
                    break

            slot_to_user[slot_id] = user_id
            print(f"✅ Assigned User {user_id} to Slot {slot_id}")
            return True

        # If the slot is occupied, try to displace the occupant
        elif occupant != user_id:  # Prevent infinite loops
            print(f"🔄 Trying to move User {occupant} to free up Slot {slot_id} for User {user_id}")

            if _find_augmenting_path(occupant, user_to_slots, slot_to_user, visited):
                # ✅ Free the previous slot
                for prev_slot, prev_user in slot_to_user.items():
                    if prev_user == user_id:
                        print(f"🔄 User {user_id} moves from Slot {prev_slot} to Slot {slot_id}")
                        slot_to_user[prev_slot] = None  # Free old slot
                        break

                print(f"✅ Moved User {occupant} to a new slot, now assigning User {user_id} to Slot {slot_id}")
                slot_to_user[slot_id] = user_id
                return True
            else:
                print(f"❌ User {occupant} could not be moved, Slot {slot_id} remains occupied")
=======

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
>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0

    return False


<<<<<<< HEAD


def max_bipartite_matching(user_to_slots, slot_to_user):
    match_count = 0
    
    # Sort user IDs in descending order so the highest ID user (4) is tried first
    for user_id in sorted(user_to_slots.keys(), reverse=True):
        visited = set()
        
        # 🚀 Debug before calling DFS
        print(f"🔍 Checking match for User {user_id}: Current Assignments = {slot_to_user}")
        
        if _find_augmenting_path(user_id, user_to_slots, slot_to_user, visited):
            match_count += 1
            
            # 🚀 Debug after finding a match
            print(f"✅ Match found! Updated Assignments = {slot_to_user}")
=======
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
>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0

    return match_count


<<<<<<< HEAD





def get_user_assignments(slot_to_user):
    """
    Invert the final slot_to_user mapping into a user->slot dict
=======
def get_user_assignments(slot_to_user):
    """
    Invert the final slot_to_user mapping into a user->slot dict
    so we can quickly see which slot a given user ended up with.
>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0
    """
    user_assignment = {}
    for slot_id, occupant in slot_to_user.items():
        if occupant is not None:
            user_assignment[occupant] = slot_id
<<<<<<< HEAD
            
    print(f"🚀 DEBUG: Final Assignments = {user_assignment}")  # Force debug print
=======
>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0
    return user_assignment





<<<<<<< HEAD
def send_notification(user_id, message, db, reschedule_id):
    notif = Notification(
        user_id=user_id,
        message=message,
        reschedule_id=reschedule_id
    )
    db.add(notif)
    db.commit()
    print(f"✅ Notification saved for User {user_id}: {message} (Reschedule ID: {reschedule_id})")


def visualize_matching_graph(user_to_slots, slot_to_user, title="Matching Graph"):
    """
    Create a bipartite graph visualization before/after matching.
    """

    G = nx.DiGraph()

    # user nodes
    for user in user_to_slots:
        G.add_node(f"User {user}", color="blue", bipartite=0)

    # slot nodes
    for slot in slot_to_user:
        G.add_node(f"Slot {slot}", color="green", bipartite=1)

    # edges for preferences
    for user, slots in user_to_slots.items():
        for slot_id in slots:
            G.add_edge(f"User {user}", f"Slot {slot_id}", color="gray")

    # edges for final assignment
    for slot_id, occupant_id in slot_to_user.items():
        if occupant_id is not None:
            G.add_edge(f"User {occupant_id}", f"Slot {slot_id}", color="red", weight=2)

    pos = nx.bipartite_layout(G, nodes=[f"User {u}" for u in user_to_slots])
    colors = [G.nodes[n]["color"] for n in G.nodes]
    edge_colors = [G[u][v]["color"] for u, v in G.edges]

    plt.figure(figsize=(10, 6))
    nx.draw(
        G, pos, with_labels=True, node_color=colors, edge_color=edge_colors,
        node_size=2000, font_size=10, font_weight="bold"
    )
    plt.title(title)

    image_path = f"{title.replace(' ', '_')}.png"
    plt.savefig(image_path)
    plt.close()
    print(f"✅ Graph saved: {image_path}")

    if os.name == "nt":  # Windows
        os.system(f"start {image_path}")
    elif os.name == "posix":  # macOS/Linux
        os.system(f"open {image_path}")


def try_single_user_bfs_in_memory(user_id: int, db: Session):
    """
    Attempt to seat this ONE user (user_id) by displacing existing occupants -- in memory only.
    Returns the new 'slot_to_user' mapping if BFS succeeded, or None if no chain found.
    Does NOT update the DB physically. That must happen after acceptance.
    """

    # 1) Build the adjacency from your existing function
    user_to_slots, slot_to_user = build_matching_graph(db)

    visited_users = set()
    visited_slots = set()
    predecessor = {}
    queue = deque()
    queue.append(("U", user_id))
    visited_users.add(user_id)

    free_slot_found = None

    while queue and (free_slot_found is None):
        node_type, node_id = queue.popleft()
        if node_type == "U":
            # BFS outward from a user node
            for slot_id in user_to_slots.get(node_id, []):
                if slot_id in visited_slots:
                    continue

                occupant = slot_to_user.get(slot_id)
                if occupant is None:
                    # Found a free slot => BFS success
                    predecessor[("S", slot_id)] = ("U", node_id)
                    free_slot_found = slot_id
                    break
                else:
                    # Slot is occupied => attempt to displace occupant
                    predecessor[("S", slot_id)] = ("U", node_id)
                    visited_slots.add(slot_id)

                    if occupant not in visited_users:
                        visited_users.add(occupant)
                        predecessor[("U", occupant)] = ("S", slot_id)
                        queue.append(("U", occupant))

    if free_slot_found is None:
        # No augmenting path
        return None

    # 2) Reconstruct path in memory & flip occupant edges
    cur_node = ("S", free_slot_found)
    while cur_node in predecessor:
        prev_node = predecessor[cur_node]
        if cur_node[0] == "S" and prev_node[0] == "U":
            occupant_user = prev_node[1]
            slot_to_user[cur_node[1]] = occupant_user
            cur_node = prev_node
        elif cur_node[0] == "U" and prev_node[0] == "S":
            old_slot_id = prev_node[1]
            slot_to_user[old_slot_id] = None
            cur_node = prev_node

    # 3) Return the new occupant arrangement in memory
    return slot_to_user
=======


def send_notification(user_id, message, db):
    """
    Stores notifications in the database and prints to console.
    """
    notification = Notification(user_id=user_id, message=message)
    db.add(notification)
    db.commit()
    print(f"✅ Notification saved for User {user_id}: {message}")



>>>>>>> c50f9b7b695724d550c0e94564b32694d02128e0
