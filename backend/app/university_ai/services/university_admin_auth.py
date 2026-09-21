from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.university_ai.models.university import UniversityMembership


GLOBAL_ADMIN_ROLES = {
    "admin",
    "super_admin",
}

UNIVERSITY_ADMIN_ROLES = {
    "admin",
    "university_admin",
    "super_admin",
}


def require_university_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in UNIVERSITY_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="University administrator access required.",
        )

    return current_user


def require_university_access(
    university_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verify that the authenticated user can access the requested university.

    Global admins retain access to every university.
    University admins must have an active membership for the
    requested university.
    """

    if current_user.role in GLOBAL_ADMIN_ROLES:
        return current_user

    if current_user.role != "university_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="University administrator access required.",
        )

    membership = (
        db.query(UniversityMembership)
        .filter(
            UniversityMembership.user_id == current_user.id,
            UniversityMembership.university_id == university_id,
            UniversityMembership.status == "active",
            UniversityMembership.role.in_(
                {"university_admin", "admin"}
            ),
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have administrator access to this university.",
        )

    return current_user
