from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class UniversityClass(Base):
    __tablename__ = "university_classes"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    department_id = Column(Integer, nullable=True, index=True)
    programme_id = Column(Integer, nullable=True, index=True)

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True, index=True)

    level = Column(String(50), nullable=True)
    section = Column(String(100), nullable=True)

    academic_session_id = Column(Integer, nullable=False, index=True)
    semester_id = Column(Integer, nullable=False, index=True)

    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CourseOffering(Base):
    __tablename__ = "university_course_offerings"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    class_id = Column(Integer, nullable=True, index=True)

    academic_session_id = Column(Integer, nullable=False, index=True)
    semester_id = Column(Integer, nullable=False, index=True)

    level = Column(String(50), nullable=True)
    section = Column(String(100), nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LecturerCourse(Base):
    __tablename__ = "university_lecturer_courses"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    lecturer_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)

    role = Column(
        String(50),
        nullable=False,
        default="lecturer",
        server_default="lecturer",
    )

    can_manage_students = Column(Boolean, nullable=False, default=True, server_default="true")
    can_manage_assessments = Column(Boolean, nullable=False, default=True, server_default="true")
    can_manage_results = Column(Boolean, nullable=False, default=True, server_default="true")

    status = Column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StudentCourse(Base):
    __tablename__ = "university_student_courses"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    course_offering_id = Column(Integer, nullable=False, index=True)

    enrollment_status = Column(
        String(50),
        nullable=False,
        default="enrolled",
        server_default="enrolled",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())