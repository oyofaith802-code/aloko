from app.database.connection import Base, engine

# Import models so SQLAlchemy registers them.
from app.business_ai.models import (
    BusinessWorkspace,
    BusinessDataset,
    BusinessMemory,
    BusinessReport,
)


print("Creating Business Reports tables...")

Base.metadata.create_all(
    bind=engine,
    tables=[
        BusinessReport.__table__,
    ],
)

print("Business Reports tables created successfully.")