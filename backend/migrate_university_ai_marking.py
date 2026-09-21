from app.database.connection import engine

from app.university_ai.models.ai_marking import (
    AssessmentQuestion,
    AssessmentSubmission,
    AIMarkingJob,
    AIMarkingResult,
)

print("Creating University AI marking tables...")

tables = [
    AssessmentQuestion,
    AssessmentSubmission,
    AIMarkingJob,
    AIMarkingResult,
]

for model in tables:
    model.__table__.create(
        bind=engine,
        checkfirst=True,
    )

print("University AI marking tables created successfully.")