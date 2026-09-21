from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.university_ai.models.university import UniversityMembership
from app.university_ai.models.people import Lecturer


GLOBAL_ADMIN_ROLES = {
    "admin",
    "super_admin",
}

UNIVERSITY_ADMIN_ROLES = {
    "admin",
    "university_admin",
    "super_admin",
}

FACULTY_ADMIN_ROLES = {
    "faculty_admin",
}

HOD_ROLES = {
    "hod",
}


def _forbidden(detail: str):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def get_active_membership(
    db: Session,
    user_id: int,
    university_id: int,
):
    return (
        db.query(UniversityMembership)
        .filter(
            UniversityMembership.user_id == user_id,
            UniversityMembership.university_id == university_id,
            UniversityMembership.status == "active",
        )
        .first()
    )


def require_university_role(
    university_id: int,
    allowed_roles: set[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require the authenticated user to hold one of the supplied
    university membership roles.

    Global admins retain access to every university.
    Other users must have an active membership for the
    requested university.
    """

    if current_user.role in GLOBAL_ADMIN_ROLES:
        return current_user

    membership = get_active_membership(
        db=db,
        user_id=current_user.id,
        university_id=university_id,
    )

    if not membership:
        _forbidden(
            "You do not have access to this university."
        )

    if membership.role not in allowed_roles:
        _forbidden(
            "You do not have the required university role."
        )

    return current_user


def require_faculty_admin(
    university_id: int,
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    University Admin/global admins can manage the whole university.

    Faculty Admin can manage only their assigned faculty.
    """

    if current_user.role in UNIVERSITY_ADMIN_ROLES:
        return current_user

    membership = get_active_membership(
        db=db,
        user_id=current_user.id,
        university_id=university_id,
    )

    if not membership:
        _forbidden(
            "You do not have access to this university."
        )

    if membership.role not in FACULTY_ADMIN_ROLES:
        _forbidden(
            "Faculty administrator access required."
        )

    if membership.faculty_id != faculty_id:
        _forbidden(
            "You do not have administrator access to this faculty."
        )

    return current_user


def require_hod(
    university_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    University Admin/global admins can manage the whole university.

    HOD can manage only their assigned department.
    """

    if current_user.role in UNIVERSITY_ADMIN_ROLES:
        return current_user

    membership = get_active_membership(
        db=db,
        user_id=current_user.id,
        university_id=university_id,
    )

    if membership and membership.role in FACULTY_ADMIN_ROLES:
        if membership.faculty_id is None:
            _forbidden(
                "Faculty administrator is not assigned to a faculty."
            )

        return current_user

    if membership and membership.role in HOD_ROLES:
        if membership.department_id != department_id:
            _forbidden(
                "You do not have administrator access to this department."
            )

        return current_user

    lecturer = (
        db.query(Lecturer)
        .filter(
            Lecturer.user_id == current_user.id,
            Lecturer.university_id == university_id,
            Lecturer.status == "active",
        )
        .first()
    )

    if lecturer and lecturer.is_department_head:
        if lecturer.department_id != department_id:
            _forbidden(
                "You do not have administrator access to this department."
            )

        return current_user

    _forbidden(
        "Head of Department access required."
    )


def require_faculty_or_university_admin(
    university_id: int,
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Allows global admins, university admins, and the Faculty Admin
    responsible for the requested faculty.
    """

    if current_user.role in UNIVERSITY_ADMIN_ROLES:
        return current_user

    membership = get_active_membership(
        db=db,
        user_id=current_user.id,
        university_id=university_id,
    )

    if not membership:
        _forbidden(
            "You do not have access to this university."
        )

    if membership.role not in FACULTY_ADMIN_ROLES:
        _forbidden(
            "Faculty administrator access required."
        )

    if membership.faculty_id != faculty_id:
        _forbidden(
            "You do not have administrator access to this faculty."
        )

    return current_user


def require_department_or_higher_admin(
    university_id: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Allows global admins, university admins, Faculty Admins,
    and HODs with appropriate scope.
    """

    if current_user.role in UNIVERSITY_ADMIN_ROLES:
        return current_user

    membership = get_active_membership(
        db=db,
        user_id=current_user.id,
        university_id=university_id,
    )

    if not membership:
        _forbidden(
            "You do not have access to this university."
        )

    if membership.role in FACULTY_ADMIN_ROLES:
        if membership.faculty_id is None:
            _forbidden(
                "Faculty administrator is not assigned to a faculty."
            )

        return current_user

    if membership.role in HOD_ROLES:
        if membership.department_id != department_id:
            _forbidden(
                "You do not have administrator access to this department."
            )

        return current_user

    lecturer = (
        db.query(Lecturer)
        .filter(
            Lecturer.user_id == current_user.id,
            Lecturer.university_id == university_id,
            Lecturer.status == "active",
        )
        .first()
    )

    if lecturer and lecturer.is_department_head:
        if lecturer.department_id != department_id:
            _forbidden(
                "You do not have administrator access to this department."
            )

        return current_user

    _forbidden(
        "Department administrator access required."
    )
