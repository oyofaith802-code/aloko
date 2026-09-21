from app.database.connection import engine

# Import all models so SQLAlchemy registers them.
from app.models import (
    User,
    Avatar,
    Voice,
    Video,
    CreatorProject,
    CreatorScene,
)

from app.business_ai.models import (
    BusinessWorkspace,
    BusinessDataset,
    BusinessMemory,
)


def main():
    print("Creating Business AI tables...")

    BusinessWorkspace.__table__.create(
        bind=engine,
        checkfirst=True,
    )

    BusinessDataset.__table__.create(
        bind=engine,
        checkfirst=True,
    )

    BusinessMemory.__table__.create(
        bind=engine,
        checkfirst=True,
    )

    print("Business AI tables created successfully.")


if __name__ == "__main__":
    main()