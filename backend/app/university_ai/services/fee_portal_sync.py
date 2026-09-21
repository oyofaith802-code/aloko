# ============================================================
# ALOKO UNIVERSITY AI
# REAL PORTAL INTEGRATION - FEES SYNC
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


def _get_fee_model():
    candidates = (
        ("app.university_ai.models.payments", "Fee"),
        ("app.university_ai.models.payment", "Fee"),
        ("app.university_ai.models.clearance", "Fee"),
    )

    for module_name, class_name in candidates:
        try:
            module = __import__(module_name, fromlist=[class_name])
            model = getattr(module, class_name, None)
            if model is not None:
                return model
        except (ImportError, AttributeError):
            continue

    raise ImportError("Aloko Fee model could not be found.")


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_fee_data(
    record: Mapping[str, Any],
    university_id: int,
) -> dict[str, Any]:

    return {
        "external_id": _clean(first_value(
            record,
            ("external_id", "id", "uuid", "fee_id", "feeId"),
        )),
        "name": _clean(first_value(
            record,
            ("name", "fee_name", "feeName", "title", "description"),
        )),
        "amount": _number(first_value(
            record,
            ("amount", "fee_amount", "feeAmount", "value", "total"),
        )),
        "session": _clean(first_value(
            record,
            ("session", "academic_session", "academicSession"),
        )),
        "semester": _clean(first_value(
            record,
            ("semester", "academic_semester", "academicSemester"),
        )),
        "level": _clean(first_value(
            record,
            ("level", "student_level", "studentLevel"),
        )),
        "category": _clean(first_value(
            record,
            ("category", "fee_category", "feeCategory", "type"),
        )),
        "status": _clean(first_value(
            record,
            ("status", "state"),
        )) or "active",
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
            UniversityPortalMapping.entity_type == "fee",
            UniversityPortalMapping.external_id == external_id,
        )
        .first()
    )


def _find_existing_fee(
    db: Session,
    Fee,
    university_id: int,
    name: str | None,
    session: str | None,
    semester: str | None,
):

    if not name:
        return None

    query = db.query(Fee).filter(
        Fee.university_id == university_id,
    )

    if hasattr(Fee, "name"):
        query = query.filter(Fee.name == name)

    if session and hasattr(Fee, "session"):
        query = query.filter(Fee.session == session)

    if semester and hasattr(Fee, "semester"):
        query = query.filter(Fee.semester == semester)

    return query.first()


def sync_fees_from_portal(
    db: Session,
    university_id: int,
    portal_config_id: int,
    *,
    endpoint: str = "/fees",
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

    Fee = _get_fee_model()

    adapter = PortalAdapter(
        base_url=portal_config.api_base_url,
        api_key=portal_config.api_key,
        client_id=portal_config.client_id,
        client_secret=portal_config.client_secret,
    )

    records = fetch_entity_collection(
        adapter,
        "fees",
        endpoint=endpoint,
        page_size=page_size,
        max_pages=max_pages,
    )

    created = 0
    updated = 0
    failed = 0

    for record in records:
        try:
            data = _build_fee_data(
                record,
                university_id,
            )

            if not data["name"]:
                raise ValueError("Fee name is required.")

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
                        db.query(Fee)
                        .filter(Fee.id == mapping.aloko_id)
                        .first()
                    )

            if existing is None:
                existing = _find_existing_fee(
                    db,
                    Fee,
                    university_id,
                    data["name"],
                    data["session"],
                    data["semester"],
                )

            values = {}

            candidates = {
                "university_id": university_id,
                "name": data["name"],
                "amount": data["amount"],
                "session": data["session"],
                "semester": data["semester"],
                "level": data["level"],
                "category": data["category"],
                "status": data["status"],
            }

            for field, value in candidates.items():
                if hasattr(Fee, field) and value is not None:
                    values[field] = value

            if existing:
                for field, value in values.items():
                    setattr(existing, field, value)

                fee = existing
                updated += 1

            else:
                fee = Fee(**values)
                db.add(fee)
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
                    mapping.aloko_id = fee.id
                else:
                    create_portal_mapping(
                        db=db,
                        university_id=university_id,
                        portal_config_id=portal_config_id,
                        entity_type="fee",
                        aloko_id=fee.id,
                        external_id=data["external_id"],
                    )

        except Exception:
            failed += 1

    db.commit()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        action="sync_fees",
        status="success" if failed == 0 else "partial",
        message=(
            "Fee sync completed. "
            f"Processed={len(records)}, "
            f"created={created}, "
            f"updated={updated}, "
            f"failed={failed}."
        ),
    )

    db.commit()

    return {
        "success": failed == 0,
        "entity": "fees",
        "processed": len(records),
        "created": created,
        "updated": updated,
        "failed": failed,
    }