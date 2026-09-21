from app.database.connection import engine, Base

# Import all University AI models so SQLAlchemy registers them.
from app.university_ai.models.course_document import CourseDocument

from app.university_ai.models.university import (
    University,
    Faculty,
    Department,
    Programme,
    Course,
    AcademicSession,
    AcademicSemester,
    UniversityMembership,
)

print("Creating University AI tables...")

Base.metadata.create_all(
    bind=engine,
    tables=[
        University.__table__,
        Faculty.__table__,
        Department.__table__,
        Programme.__table__,
        Course.__table__,
        AcademicSession.__table__,
        AcademicSemester.__table__,
        UniversityMembership.__table__,
        CourseDocument.__table__,
    ],
)

print("University AI foundation tables created successfully.")
