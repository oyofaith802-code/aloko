# ============================================================
# ALOKO UNIVERSITY AI
# REAL PORTAL INTEGRATION - COURSE SYNC
# Phase 8.6.4.1
# ============================================================

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.university_ai.models.university import Course
from app.university_ai.models.portal import UniversityPortalMapping

from app.university_ai.services.portal_adapter import (
    PortalAdapter,
    fetch_entity_collection,
    first_value,
)

from app.university_ai.services.portal_integration import (
    create_integration_log,
    create_portal_mapping,
    get_mapping_by_aloko_id,
    get_portal_config,
)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _normalize_course_code(value: Any) -> str | None:
    value = _clean_text(value)

    if not value:
        return None

    return value.upper().replace(" ", "")


def _normalize_credit_units(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _build_course_data(
    record: Mapping[str, Any],
    university_id: int,
) -> dict[str, Any]:
    external_id = first_value(
        record,
        (
            "external_id",
            "id",
            "uuid",
            "course_id",
            "courseId",
        ),
    )

    code = first_value(
        record,
        (
            "code",
            "course_code",
            "courseCode",
            "course_code",
        ),
    )

    title = first_value(
        record,
        (
            "title",
            "name",
            "course_name",
            "course_title",
            "courseName",
        ),
    )

    description = first_value(
        record,
        (
            "description",
            "course_description",
            "courseDescription",
        ),
    )

    programme_id = first_value(
        record,
        (
            "programme_id",
            "programmeId",
            "program_id",
            "programId",
        ),
    )

    department_id = first_value(
        record,
        (
            "department_id",
            "departmentId",
            "dept_id",
        ),
    )

    credit_units = first_value(
        record,
        (
            "credit_units",
            "creditUnits",
            "units",
            "credits",
            "credit",
        ),
    )

    level = first_value(
        record,
        (
            "level",
            "course_level",
            "courseLevel",
        ),
    )

    semester = first_value(
        record,
        (
            "semester",
            "academic_semester",
            "academicSemester",
        ),
    )

    status = first_value(
        record,
        (
            "status",
            "state",
        ),
    )

    return {
        "external_id": _clean_text(external_id),
        "university_id": university_id,
        "programme_id": programme_id,
        "department_id": department_id,
        "code": _normalize_course_code(code),
        "title": _clean_text(title),
        "description": _clean_text(description),
        "credit_units": _normalize_credit_units(credit_units),
        "level": _clean_text(level),
        "semester": _clean_text(semester),
        "status": _clean_text(status) or "active",
    }


def _find_existing_course(
    db: Session,
    university_id: int,
    code: str | None,
) -> Course | None:
    if not code:
        return None

    return (
        db.query(Course)
        .filter(
            Course.university_id == university_id,
            Course.code == code,
        )
        .first()
    )


def _find_by_external_mapping(
    db: Session,
    university_id: int,
    portal_config_id: int,
    external_id: str | None,
) -> Course | None:
    if not external_id:
        return None

    mapping = (
        db.query(UniversityPortalMapping)
        .filter(
            UniversityPortalMapping.university_id == university_id,
            UniversityPortalMapping.portal_config_id == portal_config_id,
            UniversityPortalMapping.entity_type == "course",
            UniversityPortalMapping.external_id == external_id,
        )
        .first()
    )

    if not mapping:
        return None

    return (
        db.query(Course)
        .filter(
            Course.id == mapping.aloko_id,
            Course.university_id == university_id,
        )
        .first()
    )


def sync_courses_from_portal(
    db: Session,
    university_id: int,
    portal_config_id: int,
    *,
    endpoint: str = "/courses",
    page_size: int = 100,
    max_pages: int = 100,
) -> dict[str, Any]:

    portal_config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not portal_config:
        raise ValueError("Portal configuration not found.")

    if not portal_config.api_base_url:
        raise ValueError("Portal API base URL is not configured.")

    adapter = PortalAdapter(
        base_url=portal_config.api_base_url,
        api_key=portal_config.api_key,
        client_id=portal_config.client_id,
        client_secret=portal_config.client_secret,
    )

    records = fetch_entity_collection(
        adapter,
        "courses",
        endpoint=endpoint,
        page_size=page_size,
        max_pages=max_pages,
    )

    created = 0
    updated = 0
    failed = 0

    for record in records:
        try:
            data = _build_course_data(
                record,
                university_id,
            )

            external_id = data["external_id"]
            code = data["code"]
            title = data["title"]

            if not code:
                raise ValueError("Course code is required.")

            if not title:
                raise ValueError(
                    f"Course title is required for {code}."
                )

            course = _find_existing_course(
                db,
                university_id,
                code,
            )

            if course is None:
                course = _find_by_external_mapping(
                    db,
                    university_id,
                    portal_config_id,
                    external_id,
                )

            if course:
                course.programme_id = data["programme_id"]
                course.department_id = data["department_id"] or course.department_id
                course.code = code
                course.title = title
                course.description = data["description"]
                course.credit_units = data["credit_units"]
                course.level = data["level"]
                course.semester = data["semester"]
                course.status = data["status"]

                updated += 1

            else:
                if not data["department_id"]:
                    raise ValueError(
                        f"Department ID is required for course {code}."
                    )

                course = Course(
                    university_id=university_id,
                    programme_id=data["programme_id"],
                    department_id=data["department_id"],
                    code=code,
                    title=title,
                    description=data["description"],
                    credit_units=data["credit_units"],
                    level=data["level"],
                    semester=data["semester"],
                    status=data["status"],
                )

                db.add(course)
                db.flush()

                created += 1

            if external_id:
                existing_mapping = (
                    db.query(UniversityPortalMapping)
                    .filter(
                        UniversityPortalMapping.university_id
                        == university_id,
                        UniversityPortalMapping.portal_config_id
                        == portal_config_id,
                        UniversityPortalMapping.entity_type
                        == "course",
                        UniversityPortalMapping.external_id
                        == external_id,
                    )
                    .first()
                )

                if existing_mapping:
                    existing_mapping.aloko_id = course.id
                else:
                    create_portal_mapping(
                        db=db,
                        university_id=university_id,
                        portal_config_id=portal_config_id,
                        entity_type="course",
                        aloko_id=course.id,
                        external_id=external_id,
                    )

        except Exception:
            failed += 1

    db.commit()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        action="sync_courses",
        status="success" if failed == 0 else "partial",
        message=(
            f"Course sync completed. "
            f"Processed={len(records)}, "
            f"created={created}, "
            f"updated={updated}, "
            f"failed={failed}."
        ),
    )

    db.commit()

    return {
        "success": failed == 0,
        "entity": "courses",
        "processed": len(records),
        "created": created,
        "updated": updated,
        "failed": failed,
    }