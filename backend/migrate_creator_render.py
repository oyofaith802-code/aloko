from sqlalchemy import text

from app.database.connection import engine


STATEMENTS = [
    """
    ALTER TABLE creator_projects
    ADD COLUMN IF NOT EXISTS render_status
    VARCHAR NOT NULL DEFAULT 'not_started'
    """,

    """
    ALTER TABLE creator_projects
    ADD COLUMN IF NOT EXISTS final_video_url
    VARCHAR
    """,

    """
    ALTER TABLE creator_projects
    ADD COLUMN IF NOT EXISTS render_error
    TEXT
    """,
]


def main():
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))

    print("Creator render migration completed successfully.")


if __name__ == "__main__":
    main()