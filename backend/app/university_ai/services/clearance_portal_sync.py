# ============================================================
# ALOKO UNIVERSITY AI
# REAL PORTAL INTEGRATION - CLEARANCE SYNC
# Phase 8.6.4.1
# ============================================================

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.university_ai.models.portal import UniversityPortalMapping
from app.university_ai.services.portal_adapter import (
    PortalAdapter,
    fetch_entity_collection,
    first_value,
)
from app.university_ai.services.portal_integration import (
    create_integration_log,
    create_portal_mapping,
    get_portal_config,
)


def _get_clearance_model():
    candidates = (
        ("app.university_ai.models.clearance", "Clearance"),
        ("app.university_ai.models.clearance", "StudentClearance"),
        ("app.university_ai.models.payments", "Clearance"),
        ("app.university_ai.models.payment", "Clearance"),
    )

    for module_name, class_name in candidates:
        try:
            module = __import__(module_name, fromlist=[class_name])
            model = getattr(module, class_name, None)
            if model is not None:
                return model
        except (ImportError, AttributeError):
            continue

    raise ImportError("Aloko Clearance model could not be found.")


def _clean(value: Any) -> str | None:
    if value is None:
        return None

    value = str(value).strip()
    return value or None


def _build_clearance_data(
    record: Mapping[str, Any],
    university_id: int,
) -> dict[str, Any]:

    return {
        "external_id": _clean(first_value(
            record,
            (
                "external_id",
                "id",
                "uuid",
                "clearance_id",
                "clearanceId",
            ),
        )),
        "student_id": first_value(
            record,
            (
                "student_id",
                "studentId",
                "aloko_student_id",
            ),
        ),
        "matric_number": _clean(first_value(
            record,
            (
                "matric_number",
                "matric",
                "matric_no",
                "registration_number",
                "reg_no",
            ),
        )),
        "stage": _clean(first_value(
            record,
            (
                "stage",
                "clearance_stage",
                "clearanceStage",
                "stage_name",
            ),
        )),
        "status": _clean(first_value(
            record,
            (
                "status",
                "state",
                "clearance_status",
                "clearanceStatus",
            ),
        )) or "pending",
        "remarks": _clean(first_value(
            record,
            (
                "remarks",
                "remark",
                "comments",
                "comment",
                "notes",
            ),
        )),
        "session": _clean(first_value(
            record,
            (
                "session",
                "academic_session",
                "academicSession",
            ),
        )),
        "semester": _clean(first_value(
            record,
            (
                "semester",
                "academic_semester",
                "academicSemester",
            ),
        )),
        "university_id": university_id,
    }


def _find_mapping(
    db: Session,
    university_id: int,
    portal_config_id: int,
    external_id: str | None,
):
    if not external_id:
        return None

    return (
        db.query(UniversityPortalMapping)
        .filter(
            UniversityPortalMapping.university_id == university_id,
            UniversityPortalMapping.portal_config_id == portal_config_id,
            UniversityPortalMapping.entity_type == "clearance",
            UniversityPortalMapping.external_id == external_id,
        )
        .first()
    )


def _find_existing_clearance(
    db: Session,
    Clearance,
    university_id: int,
    student_id: Any,
    matric_number: str | None,
    stage: str | None,
):
    query = db.query(Clearance).filter(
        Clearance.university_id == university_id,
    )

    if student_id is not None and hasattr(Clearance, "student_id"):
        query = query.filter(Clearance.student_id == student_id)

    elif matric_number and hasattr(Clearance, "matric_number"):
        query = query.filter(
            Clearance.matric_number == matric_number
        )

    if stage and hasattr(Clearance, "stage"):
        query = query.filter(Clearance.stage == stage)

    return query.first()


def sync_clearance_from_portal(
    db: Session,
    university_id: int,
    portal_config_id: int,
    *,
    endpoint: str = "/clearance",
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
        raise ValueError(
            "Portal API base URL is not configured."
        )

    Clearance = _get_clearance_model()

    adapter = PortalAdapter(
        base_url=portal_config.api_base_url,
        api_key=portal_config.api_key,
        client_id=portal_config.client_id,
        client_secret=portal_config.client_secret,
    )

    records = fetch_entity_collection(
        adapter,
        "clearance",
        endpoint=endpoint,
        page_size=page_size,
        max_pages=max_pages,
    )

    created = 0
    updated = 0
    failed = 0

    for record in records:
        try:
            data = _build_clearance_data(
                record,
                university_id,
            )

            existing = None

            if data["external_id"]:
                mapping = _find_mapping(
                    db,
                    university_id,
                    portal_config_id,
                    data["external_id"],
                )

                if mapping:
                    existing = (
                        db.query(Clearance)
                        .filter(
                            Clearance.id == mapping.aloko_id
                        )
                        .first()
                    )

            if existing is None:
                existing = _find_existing_clearance(
                    db,
                    Clearance,
                    university_id,
                    data["student_id"],
                    data["matric_number"],
                    data["stage"],
                )

            values = {}

            candidates = {
                "university_id": university_id,
                "student_id": data["student_id"],
                "matric_number": data["matric_number"],
                "stage": data["stage"],
                "status": data["status"],
                "remarks": data["remarks"],
                "session": data["session"],
                "semester": data["semester"],
            }

            for field, value in candidates.items():
                if hasattr(Clearance, field) and value is not None:
                    values[field] = value

            if existing:
                for field, value in values.items():
                    setattr(existing, field, value)

                clearance = existing
                updated += 1

            else:
                if not values.get("university_id"):
                    raise ValueError(
                        "University ID is required."
                    )

                clearance = Clearance(**values)
                db.add(clearance)
                db.flush()
                created += 1

            if data["external_id"]:
                mapping = _find_mapping(
                    db,
                    university_id,
                    portal_config_id,
                    data["external_id"],
                )

                if mapping:
                    mapping.aloko_id = clearance.id
                else:
                    create_portal_mapping(
                        db=db,
                        university_id=university_id,
                        portal_config_id=portal_config_id,
                        entity_type="clearance",
                        aloko_id=clearance.id,
                        external_id=data["external_id"],
                    )

        except Exception:
            failed += 1

    db.commit()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        action="sync_clearance",
        status="success" if failed == 0 else "partial",
        message=(
            "Clearance sync completed. "
            f"Processed={len(records)}, "
            f"created={created}, "
            f"updated={updated}, "
            f"failed={failed}."
        ),
    )

    db.commit()

    return {
        "success": failed == 0,
        "entity": "clearance",
        "processed": len(records),
        "created": created,
        "updated": updated,
        "failed": failed,
    }