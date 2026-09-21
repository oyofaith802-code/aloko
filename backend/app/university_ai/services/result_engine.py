from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.university_ai.models.assessment import (
    Assessment,
    StudentScore,
    ResultSheet,
)


# ============================================================
# DEFAULT GRADING POLICY
# ============================================================

DEFAULT_GRADING_RULES = [
    {"min": 70, "max": 100, "grade": "A", "grade_point": 5.0, "remark": "Excellent"},
    {"min": 60, "max": 69.99, "grade": "B", "grade_point": 4.0, "remark": "Very Good"},
    {"min": 50, "max": 59.99, "grade": "C", "grade_point": 3.0, "remark": "Good"},
    {"min": 45, "max": 49.99, "grade": "D", "grade_point": 2.0, "remark": "Fair"},
    {"min": 40, "max": 44.99, "grade": "E", "grade_point": 1.0, "remark": "Pass"},
    {"min": 0, "max": 39.99, "grade": "F", "grade_point": 0.0, "remark": "Fail"},
]


# ============================================================
# GRADING
# ============================================================

def get_grade(
    percentage: float,
    grading_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    rules = grading_rules or DEFAULT_GRADING_RULES

    for rule in rules:
        if rule["min"] <= percentage <= rule["max"]:
            return {
                "grade": rule["grade"],
                "grade_point": float(rule["grade_point"]),
                "remark": rule.get("remark", ""),
            }

    raise ValueError(
        f"No grading rule matches percentage {percentage}."
    )


# ============================================================
# ASSESSMENTS
# ============================================================

def get_course_assessments(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> list[Assessment]:

    return (
        db.query(Assessment)
        .filter(
            Assessment.university_id == university_id,
            Assessment.course_offering_id == course_offering_id,
            Assessment.status == "active",
        )
        .order_by(Assessment.id)
        .all()
    )


# ============================================================
# STUDENT SCORES
# ============================================================

def get_student_scores(
    db: Session,
    university_id: int,
    student_id: int,
    course_offering_id: int,
) -> list[StudentScore]:

    return (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id == university_id,
            StudentScore.student_id == student_id,
            StudentScore.course_offering_id == course_offering_id,
        )
        .all()
    )


# ============================================================
# WEIGHT VALIDATION
# ============================================================

def validate_assessment_weights(
    assessments: list[Assessment],
) -> dict[str, Any]:

    missing_weight = [
        assessment.title
        for assessment in assessments
        if assessment.weight is None
    ]

    if missing_weight:
        return {
            "valid": False,
            "message": (
                "Some assessments do not have weights configured."
            ),
            "missing_weight": missing_weight,
            "total_weight": 0,
        }

    total_weight = sum(
        float(assessment.weight)
        for assessment in assessments
    )

    if total_weight <= 0:
        return {
            "valid": False,
            "message": "Assessment weights must be greater than zero.",
            "missing_weight": [],
            "total_weight": total_weight,
        }

    if abs(total_weight - 100.0) > 0.01:
        return {
            "valid": False,
            "message": (
                f"Assessment weights must total 100%. "
                f"Current total: {total_weight}%."
            ),
            "missing_weight": [],
            "total_weight": total_weight,
        }

    return {
        "valid": True,
        "message": "Assessment weights are valid.",
        "missing_weight": [],
        "total_weight": total_weight,
    }


# ============================================================
# CALCULATE STUDENT RESULT
# ============================================================

def calculate_student_result(
    db: Session,
    university_id: int,
    student_id: int,
    course_offering_id: int,
    grading_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    assessments = get_course_assessments(
        db,
        university_id,
        course_offering_id,
    )

    if not assessments:
        raise ValueError(
            "No active assessments exist for this course."
        )

    weight_check = validate_assessment_weights(
        assessments
    )

    if not weight_check["valid"]:
        raise ValueError(weight_check["message"])

    scores = get_student_scores(
        db,
        university_id,
        student_id,
        course_offering_id,
    )

    score_map = {
        score.assessment_id: score
        for score in scores
    }

    missing_assessments = []
    assessment_results = []

    weighted_total = 0.0
    raw_total = 0.0
    raw_max = 0.0

    for assessment in assessments:

        student_score = score_map.get(
            assessment.id
        )

        if (
            student_score is None
            or student_score.score is None
        ):
            missing_assessments.append(
                assessment.title
            )
            continue

        score = float(student_score.score)
        max_score = float(assessment.max_score)
        weight = float(assessment.weight)

        if max_score <= 0:
            raise ValueError(
                f"Invalid maximum score for {assessment.title}."
            )

        percentage = (
            score / max_score
        ) * 100

        weighted_score = (
            percentage * weight
        ) / 100

        raw_total += score
        raw_max += max_score
        weighted_total += weighted_score

        assessment_results.append(
            {
                "assessment_id": assessment.id,
                "assessment": assessment.title,
                "score": score,
                "max_score": max_score,
                "percentage": percentage,
                "weight": weight,
                "weighted_score": weighted_score,
            }
        )

    if missing_assessments:
        return {
            "complete": False,
            "student_id": student_id,
            "course_offering_id": course_offering_id,
            "missing_assessments": missing_assessments,
            "assessments": assessment_results,
            "raw_total": raw_total,
            "raw_max": raw_max,
            "percentage": None,
            "grade": None,
            "grade_point": None,
            "remark": None,
        }

    percentage = round(
        weighted_total,
        2,
    )

    grade_result = get_grade(
        percentage,
        grading_rules,
    )

    return {
        "complete": True,
        "student_id": student_id,
        "course_offering_id": course_offering_id,
        "missing_assessments": [],
        "assessments": assessment_results,
        "raw_total": round(raw_total, 2),
        "raw_max": round(raw_max, 2),
        "percentage": percentage,
        "grade": grade_result["grade"],
        "grade_point": grade_result["grade_point"],
        "remark": grade_result["remark"],
    }


# ============================================================
# GENERATE RESULT SHEET
# ============================================================

def generate_result_sheet(
    db: Session,
    university_id: int,
    student_id: int,
    course_offering_id: int,
    generated_by: int | None = None,
    grading_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    result = calculate_student_result(
        db=db,
        university_id=university_id,
        student_id=student_id,
        course_offering_id=course_offering_id,
        grading_rules=grading_rules,
    )

    if not result["complete"]:
        return {
            "success": False,
            "message": (
                "Result cannot be generated because "
                "some assessments are missing."
            ),
            "result": result,
        }

    existing = (
        db.query(ResultSheet)
        .filter(
            ResultSheet.university_id == university_id,
            ResultSheet.student_id == student_id,
            ResultSheet.course_offering_id == course_offering_id,
        )
        .first()
    )

    if existing:
        result_sheet = existing
    else:
        result_sheet = ResultSheet(
            university_id=university_id,
            student_id=student_id,
            course_offering_id=course_offering_id,
        )
        db.add(result_sheet)

    result_sheet.total_score = result["raw_total"]
    result_sheet.percentage = result["percentage"]
    result_sheet.grade = result["grade"]
    result_sheet.grade_point = result["grade_point"]
    result_sheet.remarks = result["remark"]
    result_sheet.status = "draft"
    result_sheet.generated_by = generated_by

    db.commit()
    db.refresh(result_sheet)

    return {
        "success": True,
        "message": "Result sheet generated successfully.",
        "result_sheet_id": result_sheet.id,
        "result": result,
    }


# ============================================================
# GENERATE RESULTS FOR MANY STUDENTS
# ============================================================

def generate_course_results(
    db: Session,
    university_id: int,
    student_ids: list[int],
    course_offering_id: int,
    generated_by: int | None = None,
    grading_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    generated = []
    incomplete = []
    failed = []

    for student_id in student_ids:

        try:

            result = generate_result_sheet(
                db=db,
                university_id=university_id,
                student_id=student_id,
                course_offering_id=course_offering_id,
                generated_by=generated_by,
                grading_rules=grading_rules,
            )

            if result["success"]:
                generated.append(
                    {
                        "student_id": student_id,
                        "result_sheet_id":
                            result["result_sheet_id"],
                        "percentage":
                            result["result"]["percentage"],
                        "grade":
                            result["result"]["grade"],
                    }
                )

            else:
                incomplete.append(
                    {
                        "student_id": student_id,
                        "reason":
                            result["message"],
                    }
                )

        except Exception as exc:

            db.rollback()

            failed.append(
                {
                    "student_id": student_id,
                    "reason": str(exc),
                }
            )

    return {
        "success": len(failed) == 0,
        "generated": generated,
        "incomplete": incomplete,
        "failed": failed,
        "total_students": len(student_ids),
        "total_generated": len(generated),
        "total_incomplete": len(incomplete),
        "total_failed": len(failed),
    }


# ============================================================
# RESULT REVIEW
# ============================================================

def approve_result(
    db: Session,
    university_id: int,
    result_sheet_id: int,
) -> ResultSheet:

    result = (
        db.query(ResultSheet)
        .filter(
            ResultSheet.id == result_sheet_id,
            ResultSheet.university_id == university_id,
        )
        .first()
    )

    if not result:
        raise ValueError(
            "Result sheet not found."
        )

    if result.status != "draft":
        raise ValueError(
            "Only draft results can be approved."
        )

    result.status = "approved"

    db.commit()
    db.refresh(result)

    return result


# ============================================================
# RESULT PUBLICATION
# ============================================================

def publish_result(
    db: Session,
    university_id: int,
    result_sheet_id: int,
) -> ResultSheet:

    result = (
        db.query(ResultSheet)
        .filter(
            ResultSheet.id == result_sheet_id,
            ResultSheet.university_id == university_id,
        )
        .first()
    )

    if not result:
        raise ValueError(
            "Result sheet not found."
        )

    if result.status != "approved":
        raise ValueError(
            "Only approved results can be published."
        )

    from sqlalchemy.sql import func

    result.status = "published"
    result.published_at = func.now()

    db.commit()
    db.refresh(result)

    return result


# ============================================================
# RESULT RETRIEVAL
# ============================================================

def get_student_result(
    db: Session,
    university_id: int,
    student_id: int,
    course_offering_id: int,
) -> ResultSheet | None:

    return (
        db.query(ResultSheet)
        .filter(
            ResultSheet.university_id == university_id,
            ResultSheet.student_id == student_id,
            ResultSheet.course_offering_id == course_offering_id,
        )
        .first()
    )