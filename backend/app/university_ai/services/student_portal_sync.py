# ============================================================
# ALOKO UNIVERSITY AI
# STUDENT PORTAL SYNC ENGINE
# Phase 8.6.4.2
# ============================================================

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.university_ai.models.people import Student
from app.university_ai.models.portal import UniversityPortalConfig

from app.university_ai.services.portal_adapter import (
    PortalAdapter,
    fetch_entity_collection,
)

from app.university_ai.services.portal_integration import (
    complete_sync_job,
    create_integration_log,
    create_portal_mapping,
    create_sync_job,
    fail_sync_job,
    get_portal_config,
    get_portal_mapping,
    start_sync_job,
)


def _normalize_email(value: Any) -> str | None:
    if value is None:
        return None

    email = str(value).strip().lower()

    if not email or "@" not in email:
        return None

    return email


def _student_data(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "matric_number": str(
            record.get("matric_number") or ""
        ).strip().upper(),

        "first_name": str(
            record.get("first_name") or ""
        ).strip(),

        "middle_name": (
            str(record["middle_name"]).strip()
            if record.get("middle_name") is not None
            else None
        ),

        "last_name": str(
            record.get("last_name") or ""
        ).strip(),

        "level": (
            str(record["level"]).strip()
            if record.get("level") is not None
            else None
        ),

        "phone": (
            str(record["phone"]).strip()
            if record.get("phone") is not None
            else None
        ),

        "department_id": record.get("department_id"),
        "programme_id": record.get("programme_id"),
    }


def _find_student(
    db: Session,
    university_id: int,
    matric_number: str,
) -> Student | None:
    return (
        db.query(Student)
        .filter(
            Student.university_id == university_id,
            Student.matric_number == matric_number,
        )
        .first()
    )


def _find_or_create_user(
    db: Session,
    email: str | None,
) -> User | None:
    """
    Portal students may not have Aloko login accounts yet.

    We only link to an existing user by email.
    We do NOT invent passwords or mark accounts as verified.
    """

    if not email:
        return None

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    return user


def sync_students_from_portal(
    db: Session,
    *,
    university_id: int,
    portal_config_id: int,
    endpoint: str = "/students",
    page_size: int = 100,
    max_pages: int = 100,
) -> dict[str, Any]:

    config: UniversityPortalConfig | None = get_portal_config(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
    )

    if not config:
        raise ValueError(
            "Portal configuration not found."
        )

    if not config.api_base_url:
        raise ValueError(
            "Portal API base URL is not configured."
        )

    sync = create_sync_job(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        sync_type="students",
        direction="pull",
    )

    sync_id = sync.id

    try:
        start_sync_job(
            db=db,
            university_id=university_id,
            sync_id=sync_id,
        )

        adapter = PortalAdapter(
            base_url=config.api_base_url,
            api_key=config.api_key,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )

        records = fetch_entity_collection(
            adapter,
            "students",
            endpoint=endpoint,
            page_size=page_size,
            max_pages=max_pages,
        )

        created = 0
        updated = 0
        failed = 0

        for record in records:
            try:
                data = _student_data(record)

                matric_number = data["matric_number"]

                if not matric_number:
                    failed += 1
                    continue

                if not data["first_name"] or not data["last_name"]:
                    failed += 1
                    continue

                student = _find_student(
                    db,
                    university_id,
                    matric_number,
                )

                email = _normalize_email(
                    record.get("email")
                )

                user = _find_or_create_user(
                    db,
                    email,
                )

                if student:
                    student.first_name = data["first_name"]
                    student.middle_name = data["middle_name"]
                    student.last_name = data["last_name"]

                    if data["level"] is not None:
                        student.level = data["level"]

                    if data["phone"] is not None:
                        student.phone = data["phone"]

                    if data["department_id"] is not None:
                        student.department_id = data["department_id"]

                    if data["programme_id"] is not None:
                        student.programme_id = data["programme_id"]

                    if user and not student.user_id:
                        student.user_id = user.id

                    updated += 1

                else:
                    user_id = user.id if user else None

                    student = Student(
                        user_id=user_id,
                        university_id=university_id,
                        matric_number=matric_number,
                        first_name=data["first_name"],
                        middle_name=data["middle_name"],
                        last_name=data["last_name"],
                        level=data["level"],
                        phone=data["phone"],
                        department_id=data["department_id"],
                        programme_id=data["programme_id"],
                        status="active",
                    )

                    db.add(student)
                    db.flush()

                    created += 1

                external_id = (
                    record.get("external_id")
                    or record.get("id")
                    or record.get("student_id")
                )

                if external_id is not None:
                    existing_mapping = get_portal_mapping(
                        db=db,
                        university_id=university_id,
                        portal_config_id=portal_config_id,
                        entity_type="student",
                        external_id=str(external_id),
                    )

                    if not existing_mapping:
                        create_portal_mapping(
                            db=db,
                            university_id=university_id,
                            portal_config_id=portal_config_id,
                            entity_type="student",
                            aloko_id=student.id,
                            external_id=str(external_id),
                            external_reference=matric_number,
                        )

                db.commit()

            except Exception as exc:
                print(f'STUDENT SYNC ERROR: {exc}')
                db.rollback()
                failed += 1
        result = complete_sync_job(
            db=db,
            university_id=university_id,
            sync_id=sync_id,
            records_processed=len(records),
            records_created=created,
            records_updated=updated,
            records_failed=failed,
        )

        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=portal_config_id,
            action="student_sync",
            status="success",
            message=(
                f"Student sync completed. "
                f"Processed={len(records)}, "
                f"Created={created}, "
                f"Updated={updated}, "
                f"Failed={failed}."
            ),
        )

        return {
            "success": True,
            "sync": result,
            "processed": len(records),
            "created": created,
            "updated": updated,
            "failed": failed,
        }

    except Exception as exc:
        db.rollback()

        fail_sync_job(
            db=db,
            university_id=university_id,
            sync_id=sync_id,
            error_message=str(exc),
        )

        create_integration_log(
            db=db,
            university_id=university_id,
            portal_config_id=portal_config_id,
            action="student_sync",
            status="failed",
            message=str(exc),
        )

        raise

