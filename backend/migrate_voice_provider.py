from sqlalchemy import text

from app.database.connection import engine


STATEMENTS = [
    """
    ALTER TABLE voices
    ADD COLUMN IF NOT EXISTS provider_voice_id
    VARCHAR
    """,

    """
    ALTER TABLE voices
    ADD COLUMN IF NOT EXISTS status
    VARCHAR NOT NULL DEFAULT 'pending'
    """,
]


def main():
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))

    print("Voice provider migration completed successfully.")


if __name__ == "__main__":
    main()