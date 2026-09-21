from app.database.connection import engine

from app.university_ai.models.academic import (
    UniversityClass,
    CourseOffering,
    LecturerCourse,
    StudentCourse,
)

print("Creating University academic assignment tables...")

tables = [
    UniversityClass,
    CourseOffering,
    LecturerCourse,
    StudentCourse,
]

for model in tables:
    model.__table__.create(
        bind=engine,
        checkfirst=True,
    )

print("University academic assignment tables created successfully.")