from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database.connection import Base


class AttendanceRecord(Base):
    __tablename__ = "university_attendance_records"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)

    attendance_date = Column(DateTime(timezone=True), nullable=False, index=True)

    status = Column(
        String(20),
        nullable=False,
        default="present",
        index=True
    )

    note = Column(Text, nullable=True)

    marked_by = Column(Integer, nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )