from app.database.connection import engine
from app.university_ai.models.portal import (
    UniversityPortalConfig,
    UniversityPortalSync,
    UniversityPortalMapping,
    UniversityPortalWebhook,
    UniversityPortalIntegrationLog,
)

UniversityPortalConfig.__table__.create(
    bind=engine,
    checkfirst=True,
)

UniversityPortalSync.__table__.create(
    bind=engine,
    checkfirst=True,
)

UniversityPortalMapping.__table__.create(
    bind=engine,
    checkfirst=True,
)

UniversityPortalWebhook.__table__.create(
    bind=engine,
    checkfirst=True,
)

UniversityPortalIntegrationLog.__table__.create(
    bind=engine,
    checkfirst=True,
)

print("UNIVERSITY PORTAL INTEGRATION TABLES CREATED")
print("PHASE 8.6 DATABASE FOUNDATION OK")