from sqlalchemy import text

from app.database.connection import engine


STATEMENTS = [
    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email_verified
    BOOLEAN NOT NULL DEFAULT FALSE
    """,

    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS verification_code_hash
    VARCHAR
    """,

    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS verification_code_expires_at
    TIMESTAMPTZ
    """,

    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_reset_token_hash
    VARCHAR(64)
    """,

    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_reset_expires_at
    TIMESTAMPTZ
    """,

    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS google_id
    VARCHAR UNIQUE
    """,

    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS auth_provider
    VARCHAR NOT NULL DEFAULT 'email'
    """,

    """
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS updated_at
    TIMESTAMPTZ DEFAULT NOW()
    """,

    """
    ALTER TABLE users
    ALTER COLUMN password_hash DROP NOT NULL
    """,
]


def main():
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))

    print("Users table migration completed successfully.")


if __name__ == "__main__":
    main()