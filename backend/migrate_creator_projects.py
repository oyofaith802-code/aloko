from sqlalchemy import text

from app.database.connection import engine


STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS creator_projects (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL
            REFERENCES users(id)
            ON DELETE CASCADE,
        name VARCHAR NOT NULL,
        description TEXT,
        status VARCHAR NOT NULL DEFAULT 'draft',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_creator_projects_user_id
    ON creator_projects(user_id)
    """,

    """
    CREATE TABLE IF NOT EXISTS creator_scenes (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL
            REFERENCES creator_projects(id)
            ON DELETE CASCADE,
        scene_order INTEGER NOT NULL DEFAULT 1,
        script TEXT,
        avatar_id INTEGER
            REFERENCES avatars(id),
        voice_id INTEGER
            REFERENCES voices(id),
        action VARCHAR,
        environment VARCHAR,
        camera VARCHAR,
        transition VARCHAR,
        captions_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        background_music VARCHAR,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_creator_scenes_project_id
    ON creator_scenes(project_id)
    """,
]


def main():
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))

    print("Creator projects and scenes migration completed successfully.")


if __name__ == "__main__":
    main()