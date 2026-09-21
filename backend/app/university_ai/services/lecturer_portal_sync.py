from typing import Any

from sqlalchemy.orm import Session

from app.university_ai.models.people import Lecturer
from app.university_ai.services.portal_adapter import PortalAdapter, fetch_entity_collection
from app.university_ai.services.portal_integration import (
    complete_sync_job,
    create_integration_log,
    create_portal_mapping,
    fail_sync_job,
    get_portal_config,
    create_sync_job,
    start_sync_job,
)

def _clean_text(value):
    if value is None:
        return None

    value = str(value).strip()

    return value or None


def _normalize_staff_id(value):
    value = _clean_text(value)

    if not value:
        return None

    return value.upper().replace(" ", "")


def _build_lecturer_data(record):
    def first_value(data, keys):
        for key in keys:
            value = data.get(key)

            if value is not None and value != "":
                return value

        return None

    first_name = _clean_text(
        first_value(
            record,
            (
                "first_name",
                "firstname",
                "given_name",
                "firstName",
            ),
        )
    )

    last_name = _clean_text(
        first_value(
            record,
            (
                "last_name",
                "lastname",
                "surname",
                "family_name",
                "lastName",
            ),
        )
    )

    middle_name = _clean_text(
        first_value(
            record,
            (
                "middle_name",
                "middlename",
                "other_name",
                "middleName",
            ),
        )
    )

    staff_id = _normalize_staff_id(
        first_value(
            record,
            (
                "staff_number",
                "staff_id",
                "employee_id",
                "employee_no",
            ),
        )
    )

    external_id = _clean_text(
        first_value(
            record,
            (
                "external_id",
                "id",
                "uuid",
                "staff_id",
                "employee_id",
            ),
        )
    )

    email = _clean_text(
        first_value(
            record,
            (
                "email",
                "email_address",
                "emailAddress",
            ),
        )
    )

    phone = _clean_text(
        first_value(
            record,
            (
                "phone",
                "phone_number",
                "mobile",
            ),
        )
    )

    department_id = first_value(
        record,
        (
            "department_id",
            "departmentId",
            "dept_id",
        ),
    )

    faculty_id = first_value(
        record,
        (
            "faculty_id",
            "facultyId",
        ),
    )

    title = _clean_text(
        first_value(
            record,
            (
                "title",
                "academic_title",
            ),
        )
    )

    academic_rank = _clean_text(
        first_value(
            record,
            (
                "academic_rank",
                "rank",
                "designation",
            ),
        )
    )

    specialization = _clean_text(
        first_value(
            record,
            (
                "specialization",
                "specialisation",
                "area_of_specialization",
                "area_of_specialisation",
            ),
        )
    )

    status = _clean_text(
        first_value(
            record,
            (
                "status",
                "state",
            ),
        )
    ) or "active"

    return {
        "external_id": external_id,
        "staff_id": staff_id,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "department_id": department_id,
        "faculty_id": faculty_id,
        "title": title,
        "academic_rank": academic_rank,
        "specialization": specialization,
        "status": status,
    }


def _find_existing_lecturer(
    db: Session,
    *,
    university_id: int,
    staff_id: str | None,
    external_id: str | None,
):
    if staff_id:
        lecturer = (
            db.query(Lecturer)
            .filter(
                Lecturer.university_id == university_id,
                Lecturer.staff_id == staff_id,
            )
            .first()
        )

        if lecturer:
            return lecturer

    return None


def _find_by_external_mapping(
    db: Session,
    *,
    university_id: int,
    portal_config_id: int,
    external_id: str | None,
) -> Lecturer | None:

    if not external_id:
        return None

    from app.university_ai.models.portal import UniversityPortalMapping

    mapping = (
        db.query(UniversityPortalMapping)
        .filter(
            UniversityPortalMapping.university_id == university_id,
            UniversityPortalMapping.portal_config_id == portal_config_id,
            UniversityPortalMapping.entity_type == "lecturer",
            UniversityPortalMapping.external_id == external_id,
        )
        .first()
    )

    if not mapping:
        return None

    return (
        db.query(Lecturer)
        .filter(
            Lecturer.university_id == university_id,
            Lecturer.id == mapping.aloko_id,
        )
        .first()
    )


def sync_lecturers_from_portal(
    db: Session,
    *,
    university_id: int,
    portal_config_id: int,
    endpoint: str = "/lecturers",
    page_size: int = 100,
    max_pages: int = 100,
) -> dict[str, Any]:

    config = get_portal_config(
        db,
        university_id,
        portal_config_id,
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
        sync_type="lecturers",
        direction="pull",
    )

    sync_id = sync.id

    sync = start_sync_job(
        db=db,
        university_id=university_id,
        sync_id=sync_id,
    )

    try:
        adapter = PortalAdapter(
            base_url=config.api_base_url,
            api_key=config.api_key,
            client_id=config.client_id,
            client_secret=config.client_secret,
        )

        records = fetch_entity_collection(
            adapter,
            "lecturers",
            endpoint=endpoint,
            page_size=page_size,
            max_pages=max_pages,
        )

        created = 0
        updated = 0
        failed = 0
        errors: list[dict[str, Any]] = []

        for index, record in enumerate(records, start=1):

            try:
                data = _build_lecturer_data(record)

                if not data["first_name"]:
                    raise ValueError(
                        "Lecturer first name is missing."
                    )

                if not data["last_name"]:
                    raise ValueError(
                        "Lecturer last name is missing."
                    )

                existing = _find_existing_lecturer(
                    db,
                    university_id=university_id,
                    staff_id=data["staff_id"],
                    external_id=data["external_id"],
                )

                if not existing:
                    existing = _find_by_external_mapping(
                        db,
                        university_id=university_id,
                        portal_config_id=portal_config_id,
                        external_id=data["external_id"],
                    )

                if existing:
                    if data["staff_id"]:
                        existing.staff_id = data["staff_id"]

                    existing.first_name = data["first_name"]
                    existing.middle_name = data["middle_name"]
                    existing.last_name = data["last_name"]

                    if data["phone"] is not None:
                        existing.phone = data["phone"]

                    if data["department_id"] is not None:
                        existing.department_id = data["department_id"]

                    if data["faculty_id"] is not None:
                        existing.faculty_id = data["faculty_id"]

                    if data["title"] is not None:
                        existing.title = data["title"]

                    if data["academic_rank"] is not None:
                        existing.academic_rank = data["academic_rank"]

                    if data["specialization"] is not None:
                        existing.specialization = data["specialization"]

                    if data["status"]:
                        existing.status = data["status"]

                    updated += 1

                else:
                    lecturer = Lecturer(
                        user_id=None,
                        university_id=university_id,
                        faculty_id=data["faculty_id"],
                        department_id=data["department_id"],
                        staff_id=data["staff_id"],
                        first_name=data["first_name"],
                        middle_name=data["middle_name"],
                        last_name=data["last_name"],
                        title=data["title"],
                        academic_rank=data["academic_rank"],
                        specialization=data["specialization"],
                        phone=data["phone"],
                        status=data["status"],
                    )

                    db.add(lecturer)
                    db.flush()

                    created += 1

                    if data["external_id"]:
                        create_portal_mapping(
                            db=db,
                            university_id=university_id,
                            portal_config_id=portal_config_id,
                            entity_type="lecturer",
                            aloko_id=lecturer.id,
                            external_id=data["external_id"],
                        )

            except Exception as exc:
                failed += 1

                errors.append(
                    {
                        "record": index,
                        "error": str(exc),
                    }
                )

        db.commit()

        complete_sync_job(
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
            action="sync_lecturers",
            status="success" if failed == 0 else "partial",
            message=(
                f"Lecturer sync completed. "
                f"processed={len(records)}, "
                f"created={created}, "
                f"updated={updated}, "
                f"failed={failed}"
            ),
        )

        return {
            "success": True,
            "entity": "lecturers",
            "processed": len(records),
            "created": created,
            "updated": updated,
            "failed": failed,
            "errors": errors,
        }

    except Exception:
        db.rollback()

        try:
            fail_sync_job(
                db=db,
                university_id=university_id,
                sync_id=sync_id,
                error_message='Lecturer portal synchronization failed.',
            )
            db.commit()
        except Exception:
            db.rollback()

        raise