from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

from app.database.connection import Base


class Student(Base):
    __tablename__ = "university_students"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True, unique=True, index=True)
    university_id = Column(Integer, nullable=False, index=True)

    faculty_id = Column(Integer, nullable=True, index=True)
    department_id = Column(Integer, nullable=True, index=True)
    programme_id = Column(Integer, nullable=True, index=True)

    matric_number = Column(String(100), nullable=False, index=True)

    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)

    level = Column(String(50), nullable=True)

    entry_year = Column(Integer, nullable=True)
    graduation_year = Column(Integer, nullable=True)

    phone = Column(String(50), nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Lecturer(Base):
    __tablename__ = "university_lecturers"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True, unique=True, index=True)
    university_id = Column(Integer, nullable=False, index=True)

    faculty_id = Column(Integer, nullable=True, index=True)
    department_id = Column(Integer, nullable=True, index=True)

    staff_id = Column(String(100), nullable=True, index=True)

    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)

    title = Column(String(100), nullable=True)
    academic_rank = Column(String(100), nullable=True)

    specialization = Column(Text, nullable=True)

    phone = Column(String(50), nullable=True)

    is_department_head = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
