# ============================================================
# ALOKO UNIVERSITY AI
# REAL PORTAL INTEGRATION - RESULTS SYNC
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

# IMPORTANT:
# Result/assessment models can differ between existing Aloko builds.
# This engine resolves the model dynamically so the portal adapter
# does not break if the result model name changes.


def _get_result_model():
    candidates = (
        ("app.university_ai.models.results", "Result"),
        ("app.university_ai.models.assessment", "Result"),
        ("app.university_ai.models.academic", "Result"),
    )

    for module_name, class_name in candidates:
        try:
            module = __import__(
                module_name,
                fromlist=[class_name],
            )
            model = getattr(module, class_name, None)
            if model is not None:
                return model
        except (ImportError, AttributeError):
            continue

    raise ImportError(
        "Aloko Result model could not be found."
    )


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _build_result_data(
    record: Mapping[str, Any],
    university_id: int,
) -> dict[str, Any]:

    external_id = first_value(
        record,
        (
            "external_id",
            "id",
            "uuid",
            "result_id",
            "resultId",
        ),
    )

    student_external_id = first_value(
        record,
        (
            "student_id",
            "studentId",
            "student_external_id",
            "studentExternalId",
        ),
    )

    matric_number = first_value(
        record,
        (
            "matric_number",
            "matric",
            "matric_no",
            "registration_number",
            "reg_no",
        ),
    )

    course_external_id = first_value(
        record,
        (
            "course_id",
            "courseId",
            "course_external_id",
            "courseExternalId",
        ),
    )

    course_code = first_value(
        record,
        (
            "course_code",
            "courseCode",
            "code",
        ),
    )

    session = first_value(
        record,
        (
            "session",
            "academic_session",
            "academicSession",
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

    score = first_value(
        record,
        (
            "score",
            "marks",
            "mark",
            "total_score",
            "totalScore",
            "value",
        ),
    )

    grade = first_value(
        record,
        (
            "grade",
            "letter_grade",
            "letterGrade",
        ),
    )

    grade_point = first_value(
        record,
        (
            "grade_point",
            "gradePoint",
            "points",
        ),
    )

    credit_units = first_value(
        record,
        (
            "credit_units",
            "creditUnits",
            "units",
            "credits",
        ),
    )

    assessment_id = first_value(
        record,
        (
            "assessment_id",
            "assessmentId",
        ),
    )

    return {
        "external_id": _clean_text(external_id),
        "student_external_id": _clean_text(student_external_id),
        "matric_number": _clean_text(matric_number),
        "course_external_id": _clean_text(course_external_id),
        "course_code": _clean_text(course_code),
        "university_id": university_id,
        "session": _clean_text(session),
        "semester": _clean_text(semester),
        "score": _to_float(score),
        "grade": _clean_text(grade),
        "grade_point": _to_float(grade_point),
        "credit_units": _to_int(credit_units),
        "assessment_id": _to_int(assessment_id),
    }


def _find_mapping(
    db: Session,
    university_id: int,
    portal_config_id: int,
    entity_type: str,
    external_id: str | None,
):
    if not external_id:
        return None

    return (
        db.query(UniversityPortalMapping)
        .filter(
            UniversityPortalMapping.university_id == university_id,
            UniversityPortalMapping.portal_config_id == portal_config_id,
            UniversityPortalMapping.entity_type == entity_type,
            UniversityPortalMapping.external_id == external_id,
        )
        .first()
    )


def _resolve_student_id(
    db: Session,
    university_id: int,
    portal_config_id: int,
    student_external_id: str | None,
    matric_number: str | None,
) -> int | None:

    mapping = _find_mapping(
        db,
        university_id,
        portal_config_id,
        "student",
        student_external_id,
    )

    if mapping:
        return mapping.aloko_id

    if not matric_number:
        return None

    try:
        from app.university_ai.models.people import Student

        student = (
            db.query(Student)
            .filter(
                Student.university_id == university_id,
                Student.matric_number == matric_number,
            )
            .first()
        )

        return student.id if student else None

    except ImportError:
        return None


def _resolve_course_id(
    db: Session,
    university_id: int,
    portal_config_id: int,
    course_external_id: str | None,
    course_code: str | None,
) -> int | None:

    mapping = _find_mapping(
        db,
        university_id,
        portal_config_id,
        "course",
        course_external_id,
    )

    if mapping:
        return mapping.aloko_id

    if not course_code:
        return None

    try:
        from app.university_ai.models.university import Course

        course = (
            db.query(Course)
            .filter(
                Course.university_id == university_id,
                Course.code == course_code.upper().replace(" ", ""),
            )
            .first()
        )

        return course.id if course else None

    except ImportError:
        return None


def _find_existing_result(
    db: Session,
    Result,
    university_id: int,
    student_id: int,
    course_id: int,
    session: str | None,
    semester: str | None,
):

    query = db.query(Result).filter(
        Result.university_id == university_id,
        Result.student_id == student_id,
        Result.course_id == course_id,
    )

    if session and hasattr(Result, "session"):
        query = query.filter(Result.session == session)

    if semester and hasattr(Result, "semester"):
        query = query.filter(Result.semester == semester)

    return query.first()


def sync_results_from_portal(
    db: Session,
    university_id: int,
    portal_config_id: int,
    *,
    endpoint: str = "/results",
    page_size: int = 100,
    max_pages: int = 100,
) -> dict[str, Any]:

    portal_config = get_portal_config(
        db,
        university_id,
        portal_config_id,
    )

    if not portal_config:
        raise ValueError(
            "Portal configuration not found."
        )

    if not portal_config.api_base_url:
        raise ValueError(
            "Portal API base URL is not configured."
        )

    Result = _get_result_model()

    adapter = PortalAdapter(
        base_url=portal_config.api_base_url,
        api_key=portal_config.api_key,
        client_id=portal_config.client_id,
        client_secret=portal_config.client_secret,
    )

    records = fetch_entity_collection(
        adapter,
        "results",
        endpoint=endpoint,
        page_size=page_size,
        max_pages=max_pages,
    )

    created = 0
    updated = 0
    failed = 0

    for record in records:
        try:
            data = _build_result_data(
                record,
                university_id,
            )

            student_id = _resolve_student_id(
                db,
                university_id,
                portal_config_id,
                data["student_external_id"],
                data["matric_number"],
            )

            course_id = _resolve_course_id(
                db,
                university_id,
                portal_config_id,
                data["course_external_id"],
                data["course_code"],
            )

            if not student_id:
                raise ValueError(
                    "Student could not be resolved."
                )

            if not course_id:
                raise ValueError(
                    "Course could not be resolved."
                )

            result = None

            external_id = data["external_id"]

            if external_id:
                mapping = _find_mapping(
                    db,
                    university_id,
                    portal_config_id,
                    "result",
                    external_id,
                )

                if mapping:
                    result = (
                        db.query(Result)
                        .filter(
                            Result.id == mapping.aloko_id
                        )
                        .first()
                    )

            if result is None:
                result = _find_existing_result(
                    db,
                    Result,
                    university_id,
                    student_id,
                    course_id,
                    data["session"],
                    data["semester"],
                )

            values = {}

            candidate_fields = {
                "university_id": university_id,
                "student_id": student_id,
                "course_id": course_id,
                "session": data["session"],
                "semester": data["semester"],
                "score": data["score"],
                "grade": data["grade"],
                "grade_point": data["grade_point"],
                "credit_units": data["credit_units"],
                "assessment_id": data["assessment_id"],
            }

            for field, value in candidate_fields.items():
                if hasattr(Result, field) and value is not None:
                    values[field] = value

            if result:

                for field, value in values.items():
                    setattr(result, field, value)

                updated += 1

            else:

                result = Result(**values)

                db.add(result)
                db.flush()

                created += 1

            if external_id:

                mapping = _find_mapping(
                    db,
                    university_id,
                    portal_config_id,
                    "result",
                    external_id,
                )

                if mapping:
                    mapping.aloko_id = result.id

                else:
                    create_portal_mapping(
                        db=db,
                        university_id=university_id,
                        portal_config_id=portal_config_id,
                        entity_type="result",
                        aloko_id=result.id,
                        external_id=external_id,
                    )

        except Exception:
            failed += 1

    db.commit()

    create_integration_log(
        db=db,
        university_id=university_id,
        portal_config_id=portal_config_id,
        action="sync_results",
        status="success" if failed == 0 else "partial",
        message=(
            "Result sync completed. "
            f"Processed={len(records)}, "
            f"created={created}, "
            f"updated={updated}, "
            f"failed={failed}."
        ),
    )

    db.commit()

    return {
        "success": failed == 0,
        "entity": "results",
        "processed": len(records),
        "created": created,
        "updated": updated,
        "failed": failed,
    }