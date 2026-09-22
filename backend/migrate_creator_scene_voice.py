from sqlalchemy import text
from app.database.connection import engine

STATEMENTS = [
    """
    ALTER TABLE creator_scenes
    ADD COLUMN IF NOT EXISTS voice VARCHAR
    """,
]

def main():
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))

    print("Creator scene voice column migration completed successfully.")

if __name__ == "__main__":
    main()
