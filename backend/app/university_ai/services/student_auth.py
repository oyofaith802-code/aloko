from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.university_ai.models.people import Student


def require_student(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Student:
    student = (
        db.query(Student)
        .filter(
            Student.user_id == current_user.id,
            Student.status == "active",
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student account is not linked to an active university student record.",
        )

    return student
