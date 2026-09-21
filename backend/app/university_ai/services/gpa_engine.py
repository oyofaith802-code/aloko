from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.university_ai.models.assessment import ResultSheet


# ============================================================
# VALIDATION
# ============================================================

def validate_grade_point(
    grade_point: float | None,
) -> float:

    if grade_point is None:
        return 0.0

    value = float(grade_point)

    if value < 0:
        raise ValueError("Grade point cannot be negative.")

    return value


def validate_credit_units(
    credit_units: int | None,
) -> int:

    if credit_units is None:
        return 0

    value = int(credit_units)

    if value < 0:
        raise ValueError("Credit units cannot be negative.")

    return value


# ============================================================
# GPA CALCULATION
# ============================================================

def calculate_gpa_from_results(
    results: list[ResultSheet],
) -> dict[str, Any]:

    total_quality_points = 0.0
    total_credit_units = 0
    courses = []

    for result in results:

        # Only usable results participate in GPA.
        if result.status not in (
            "approved",
            "published",
        ):
            continue

        credit_units = validate_credit_units(
            result.credit_units
        )

        grade_point = validate_grade_point(
            result.grade_point
        )

        if credit_units <= 0:
            continue

        quality_points = (
            grade_point * credit_units
        )

        total_quality_points += quality_points
        total_credit_units += credit_units

        courses.append(
            {
                "result_sheet_id": result.id,
                "course_offering_id":
                    result.course_offering_id,
                "credit_units": credit_units,
                "grade": result.grade,
                "grade_point": grade_point,
                "quality_points": quality_points,
            }
        )

    if total_credit_units == 0:
        return {
            "gpa": 0.0,
            "total_quality_points": 0.0,
            "total_credit_units": 0,
            "courses": courses,
        }

    gpa = (
        total_quality_points
        / total_credit_units
    )

    return {
        "gpa": round(gpa, 2),
        "total_quality_points":
            round(total_quality_points, 2),
        "total_credit_units":
            total_credit_units,
        "courses": courses,
    }


# ============================================================
# SEMESTER GPA
# ============================================================

def calculate_semester_gpa(
    db: Session,
    university_id: int,
    student_id: int,
    course_offering_ids: list[int],
) -> dict[str, Any]:

    if not course_offering_ids:
        return {
            "gpa": 0.0,
            "total_quality_points": 0.0,
            "total_credit_units": 0,
            "courses": [],
        }

    results = (
        db.query(ResultSheet)
        .filter(
            ResultSheet.university_id == university_id,
            ResultSheet.student_id == student_id,
            ResultSheet.course_offering_id.in_(
                course_offering_ids
            ),
        )
        .all()
    )

    return calculate_gpa_from_results(results)


# ============================================================
# CGPA
# ============================================================

def calculate_cgpa(
    db: Session,
    university_id: int,
    student_id: int,
) -> dict[str, Any]:

    results = (
        db.query(ResultSheet)
        .filter(
            ResultSheet.university_id == university_id,
            ResultSheet.student_id == student_id,
        )
        .all()
    )

    result = calculate_gpa_from_results(results)

    return {
        "cgpa": result["gpa"],
        "total_quality_points":
            result["total_quality_points"],
        "total_credit_units":
            result["total_credit_units"],
        "courses": result["courses"],
    }


# ============================================================
# ACADEMIC STANDING
# ============================================================

def get_academic_standing(
    cgpa: float,
) -> str:

    if cgpa >= 4.50:
        return "First Class"

    if cgpa >= 3.50:
        return "Second Class Upper"

    if cgpa >= 2.40:
        return "Second Class Lower"

    if cgpa >= 1.50:
        return "Third Class"

    if cgpa >= 1.00:
        return "Pass"

    return "Academic Probation"


# ============================================================
# COMPLETE ACADEMIC SUMMARY
# ============================================================

def get_academic_summary(
    db: Session,
    university_id: int,
    student_id: int,
) -> dict[str, Any]:

    cgpa_result = calculate_cgpa(
        db=db,
        university_id=university_id,
        student_id=student_id,
    )

    cgpa = cgpa_result["cgpa"]

    return {
        "student_id": student_id,
        "cgpa": cgpa,
        "total_quality_points":
            cgpa_result["total_quality_points"],
        "total_credit_units":
            cgpa_result["total_credit_units"],
        "academic_standing":
            get_academic_standing(cgpa),
        "courses":
            cgpa_result["courses"],
    }


# ============================================================
# COURSE RESULT SUMMARY
# ============================================================

def get_result_summary(
    db: Session,
    university_id: int,
    student_id: int,
) -> dict[str, Any]:

    results = (
        db.query(ResultSheet)
        .filter(
            ResultSheet.university_id == university_id,
            ResultSheet.student_id == student_id,
        )
        .order_by(ResultSheet.id)
        .all()
    )

    courses = []

    for result in results:

        courses.append(
            {
                "result_sheet_id": result.id,
                "course_offering_id":
                    result.course_offering_id,
                "total_score":
                    result.total_score,
                "percentage":
                    result.percentage,
                "grade":
                    result.grade,
                "grade_point":
                    result.grade_point,
                "credit_units":
                    result.credit_units,
                "remarks":
                    result.remarks,
                "status":
                    result.status,
            }
        )

    return {
        "student_id": student_id,
        "total_results": len(courses),
        "courses": courses,
    }