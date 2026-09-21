from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func

from app.database.connection import Base


class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=True, index=True)
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active", server_default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Faculty(Base):
    __tablename__ = "university_faculties"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active", server_default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Department(Base):
    __tablename__ = "university_departments"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, nullable=False, index=True)
    university_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active", server_default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Programme(Base):
    __tablename__ = "university_programmes"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, nullable=False, index=True)
    faculty_id = Column(Integer, nullable=False, index=True)
    university_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True)
    degree_type = Column(String(100), nullable=True)
    duration_years = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="active", server_default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Course(Base):
    __tablename__ = "university_courses"

    id = Column(Integer, primary_key=True, index=True)
    programme_id = Column(Integer, nullable=True, index=True)
    department_id = Column(Integer, nullable=False, index=True)
    university_id = Column(Integer, nullable=False, index=True)

    code = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    credit_units = Column(Integer, nullable=True)
    level = Column(String(50), nullable=True)
    semester = Column(String(50), nullable=True)

    status = Column(String(50), nullable=False, default="active", server_default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AcademicSession(Base):
    __tablename__ = "academic_sessions"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, nullable=False, index=True)

    name = Column(String(100), nullable=False)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)

    is_current = Column(Boolean, nullable=False, default=False, server_default="false")
    status = Column(String(50), nullable=False, default="active", server_default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AcademicSemester(Base):
    __tablename__ = "academic_semesters"

    id = Column(Integer, primary_key=True, index=True)
    academic_session_id = Column(Integer, nullable=False, index=True)
    university_id = Column(Integer, nullable=False, index=True)

    name = Column(String(100), nullable=False)
    number = Column(Integer, nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    is_current = Column(Boolean, nullable=False, default=False, server_default="false")
    status = Column(String(50), nullable=False, default="active", server_default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UniversityMembership(Base):
    __tablename__ = "university_memberships"

    id = Column(Integer, primary_key=True, index=True)

    university_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    role = Column(String(50), nullable=False, index=True)

    faculty_id = Column(Integer, nullable=True, index=True)
    department_id = Column(Integer, nullable=True, index=True)
    programme_id = Column(Integer, nullable=True, index=True)

    member_id = Column(String(100), nullable=True, index=True)

    status = Column(String(50), nullable=False, default="active", server_default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())