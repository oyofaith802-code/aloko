from sqlalchemy import text

from app.database.connection import engine


print("Adding submission_ids to University AI marking jobs...")

with engine.begin() as connection:
    connection.execute(
        text(
            """
            ALTER TABLE university_ai_marking_jobs
            ADD COLUMN IF NOT EXISTS submission_ids TEXT
            """
        )
    )

print("submission_ids column added successfully.")
