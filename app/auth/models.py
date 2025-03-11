from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum,Time
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime,time


Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum("student", "professor", name="user_roles"), nullable=False)

    # Relationships for different user roles
    slots = relationship("SlotTime", back_populates="professor", foreign_keys="SlotTime.professor_id")
    meetings_as_student = relationship("Meeting", back_populates="student", foreign_keys="Meeting.student_id")
    meetings_as_professor = relationship("Meeting", back_populates="professor", foreign_keys="Meeting.professor_id")
    waiting_slots = relationship("WaitList", back_populates="user")
    preferred_times = relationship("PreferredTime", back_populates="user")
    notifications = relationship("Notification", back_populates="user")



class SlotTime(Base):
    __tablename__ = "slot_times"

    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)

    professor = relationship("User", back_populates="slots", foreign_keys=[professor_id])
    waiting_users = relationship("WaitList", back_populates="slot")


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slot_times.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    professor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_details = Column(String)

    slot = relationship("SlotTime")
    student = relationship("User", back_populates="meetings_as_student", foreign_keys=[student_id])
    professor = relationship("User", back_populates="meetings_as_professor", foreign_keys=[professor_id])

class WaitList(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slot_times.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # If you want relationship backrefs
    slot = relationship("SlotTime", back_populates="waiting_users")
    user = relationship("User", back_populates="waiting_slots")


class PreferredTime(Base):
    __tablename__ = "preferred_times"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    time_slot = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="preferred_times")

class RescheduleRequest(Base):
    __tablename__ = "reschedule_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_slot_id = Column(Integer, ForeignKey("slot_times.id"), nullable=False)
    new_slot_id = Column(Integer, ForeignKey("slot_times.id"), nullable=False)
    professor_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ✅ Add this column
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    professor = relationship("User", foreign_keys=[professor_id])
    current_slot = relationship("SlotTime", foreign_keys=[current_slot_id])
    new_slot = relationship("SlotTime", foreign_keys=[new_slot_id])



class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")