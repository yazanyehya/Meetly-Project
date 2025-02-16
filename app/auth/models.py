from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import declarative_base, relationship

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


class SlotTime(Base):
    __tablename__ = "slot_times"

    id = Column(Integer, primary_key=True, index=True)
    professor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)

    professor = relationship("User", back_populates="slots", foreign_keys=[professor_id])


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
