from app.database.connection import engine

from app.university_ai.models.people import (
    Student,
    Lecturer,
)

print("Creating University Student/Lecturer tables...")

Student.__table__.create(
    bind=engine,
    checkfirst=True,
)

Lecturer.__table__.create(
    bind=engine,
    checkfirst=True,
)

print("Student and Lecturer tables created successfully.")