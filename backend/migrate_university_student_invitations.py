from app.database.connection import engine
from app.university_ai.models.student_invitation import StudentInvitation

print("Creating University Student Invitation table...")

StudentInvitation.__table__.create(
    bind=engine,
    checkfirst=True,
)

print("University Student Invitation table created successfully.")
