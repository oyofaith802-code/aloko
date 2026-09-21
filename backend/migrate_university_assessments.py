from app.database.connection import engine

from app.university_ai.models.assessment import (
    Assessment,
    StudentScore,
    ResultSheet,
)

print("Creating University assessment tables...")

tables = [
    Assessment,
    StudentScore,
    ResultSheet,
]

for model in tables:
    model.__table__.create(
        bind=engine,
        checkfirst=True,
    )

print("University assessment tables created successfully.")