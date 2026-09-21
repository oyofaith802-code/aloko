from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.university_ai.models.people import Lecturer


def require_lecturer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Lecturer:
    lecturer = (
        db.query(Lecturer)
        .filter(
            Lecturer.user_id == current_user.id,
            Lecturer.status == "active",
        )
        .first()
    )

    if not lecturer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lecturer account is not linked to a university lecturer record.",
        )

    return lecturer