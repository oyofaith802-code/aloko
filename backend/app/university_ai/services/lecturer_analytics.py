from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.university_ai.models import (
    Student,
    StudentCourse,
    StudentScore,
    Assessment,
)


# ============================================================
# BASIC HELPERS
# ============================================================

def _get_course_students(
    db: Session,
    university_id: int,
    course_offering_id: int,
):
    return (
        db.query(Student)
        .join(
            StudentCourse,
            StudentCourse.student_id == Student.id,
        )
        .filter(
            StudentCourse.university_id == university_id,
            StudentCourse.course_offering_id
            == course_offering_id,
            StudentCourse.enrollment_status == "enrolled",
            Student.university_id == university_id,
            Student.status == "active",
        )
        .all()
    )


def _get_course_assessments(
    db: Session,
    university_id: int,
    course_offering_id: int,
):
    return (
        db.query(Assessment)
        .filter(
            Assessment.university_id == university_id,
            Assessment.course_offering_id
            == course_offering_id,
            Assessment.status == "active",
        )
        .all()
    )


def _get_course_scores(
    db: Session,
    university_id: int,
    course_offering_id: int,
):
    return (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id == university_id,
            StudentScore.course_offering_id
            == course_offering_id,
        )
        .all()
    )


# ============================================================
# CLASS PERFORMANCE
# ============================================================

def get_class_performance(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> dict[str, Any]:

    students = _get_course_students(
        db,
        university_id,
        course_offering_id,
    )

    assessments = _get_course_assessments(
        db,
        university_id,
        course_offering_id,
    )

    scores = _get_course_scores(
        db,
        university_id,
        course_offering_id,
    )

    score_map = {
        (
            score.student_id,
            score.assessment_id,
        ): score
        for score in scores
    }

    student_totals = []

    for student in students:

        total = 0.0
        completed = True

        for assessment in assessments:

            score = score_map.get(
                (
                    student.id,
                    assessment.id,
                )
            )

            if score is None:
                completed = False
                continue

            if score.percentage is not None:
                weight = (
                    float(assessment.weight)
                    if assessment.weight is not None
                    else 0.0
                )

                total += (
                    score.percentage
                    * weight
                    / 100
                )

        student_totals.append(
            {
                "student_id": student.id,
                "matric_number":
                    student.matric_number,
                "student_name":
                    f"{student.first_name} "
                    f"{student.last_name}",
                "total_score":
                    round(total, 2),
                "complete":
                    completed,
            }
        )

    complete_scores = [
        item["total_score"]
        for item in student_totals
        if item["complete"]
    ]

    if not complete_scores:
        return {
            "course_offering_id":
                course_offering_id,
            "student_count":
                len(students),
            "completed_students": 0,
            "average_score": 0.0,
            "highest_score": 0.0,
            "lowest_score": 0.0,
            "pass_count": 0,
            "fail_count": 0,
            "pass_rate": 0.0,
            "fail_rate": 0.0,
            "students": student_totals,
        }

    average = sum(
        complete_scores
    ) / len(complete_scores)

    highest = max(complete_scores)
    lowest = min(complete_scores)

    pass_count = sum(
        1
        for score in complete_scores
        if score >= 40
    )

    fail_count = (
        len(complete_scores)
        - pass_count
    )

    return {
        "course_offering_id":
            course_offering_id,

        "student_count":
            len(students),

        "completed_students":
            len(complete_scores),

        "average_score":
            round(average, 2),

        "highest_score":
            round(highest, 2),

        "lowest_score":
            round(lowest, 2),

        "pass_count":
            pass_count,

        "fail_count":
            fail_count,

        "pass_rate":
            round(
                pass_count
                / len(complete_scores)
                * 100,
                2,
            ),

        "fail_rate":
            round(
                fail_count
                / len(complete_scores)
                * 100,
                2,
            ),

        "students":
            student_totals,
    }


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

def get_score_distribution(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> dict[str, int]:

    performance = get_class_performance(
        db,
        university_id,
        course_offering_id,
    )

    distribution = {
        "A_70_100": 0,
        "B_60_69": 0,
        "C_50_59": 0,
        "D_45_49": 0,
        "E_40_44": 0,
        "F_0_39": 0,
    }

    for student in performance["students"]:

        if not student["complete"]:
            continue

        score = student["total_score"]

        if score >= 70:
            distribution["A_70_100"] += 1
        elif score >= 60:
            distribution["B_60_69"] += 1
        elif score >= 50:
            distribution["C_50_59"] += 1
        elif score >= 45:
            distribution["D_45_49"] += 1
        elif score >= 40:
            distribution["E_40_44"] += 1
        else:
            distribution["F_0_39"] += 1

    return distribution


# ============================================================
# INDIVIDUAL STUDENT PERFORMANCE
# ============================================================

def get_student_performance(
    db: Session,
    university_id: int,
    course_offering_id: int,
    student_id: int,
) -> dict[str, Any]:

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id,
            Student.university_id == university_id,
        )
        .first()
    )

    if not student:
        raise ValueError("Student not found.")

    assessments = _get_course_assessments(
        db,
        university_id,
        course_offering_id,
    )

    scores = (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id == university_id,
            StudentScore.student_id == student_id,
            StudentScore.course_offering_id
            == course_offering_id,
        )
        .all()
    )

    score_map = {
        score.assessment_id: score
        for score in scores
    }

    assessment_results = []
    weighted_total = 0.0

    for assessment in assessments:

        score = score_map.get(assessment.id)

        percentage = (
            score.percentage
            if score
            and score.percentage is not None
            else None
        )

        weighted_score = None

        if percentage is not None:
            weight = (
                float(assessment.weight)
                if assessment.weight is not None
                else 0.0
            )

            weighted_score = (
                percentage
                * weight
                / 100
            )

            weighted_total += weighted_score

        assessment_results.append(
            {
                "assessment_id":
                    assessment.id,
                "title":
                    assessment.title,
                "assessment_type":
                    assessment.assessment_type,
                "max_score":
                    assessment.max_score,
                "score":
                    score.score
                    if score
                    else None,
                "percentage":
                    percentage,
                "weight":
                    assessment.weight,
                "weighted_score":
                    (
                        round(
                            weighted_score,
                            2,
                        )
                        if weighted_score
                        is not None
                        else None
                    ),
                "status":
                    score.status
                    if score
                    else "missing",
            }
        )

    return {
        "student_id": student.id,
        "matric_number":
            student.matric_number,
        "student_name":
            f"{student.first_name} "
            f"{student.last_name}",
        "total_score":
            round(weighted_total, 2),
        "assessments":
            assessment_results,
    }


# ============================================================
# STRENGTHS AND WEAKNESSES
# ============================================================

def analyze_student_strengths(
    performance: dict[str, Any],
) -> dict[str, list[str]]:

    strong = []
    weak = []

    for assessment in performance["assessments"]:

        percentage = assessment["percentage"]

        if percentage is None:
            continue

        if percentage >= 70:
            strong.append(
                assessment["title"]
            )

        elif percentage < 50:
            weak.append(
                assessment["title"]
            )

    return {
        "strengths": strong,
        "weaknesses": weak,
    }


# ============================================================
# AT-RISK STUDENTS
# ============================================================

def get_at_risk_students(
    db: Session,
    university_id: int,
    course_offering_id: int,
    threshold: float = 40.0,
) -> list[dict[str, Any]]:

    performance = get_class_performance(
        db,
        university_id,
        course_offering_id,
    )

    at_risk = []

    for student in performance["students"]:

        if not student["complete"]:
            at_risk.append(
                {
                    **student,
                    "risk_reason":
                        "Incomplete assessment records.",
                }
            )
            continue

        if student["total_score"] < threshold:
            at_risk.append(
                {
                    **student,
                    "risk_reason":
                        "Current performance is below "
                        "the configured threshold.",
                }
            )

    return at_risk


# ============================================================
# AUTOMATIC REMARK
# ============================================================

def generate_student_remark(
    score: float,
) -> str:

    score = float(score)

    if score >= 70:
        return (
            "Excellent performance. "
            "The student demonstrates strong "
            "understanding of the course."
        )

    if score >= 60:
        return (
            "Very good performance. "
            "The student demonstrates good "
            "understanding of the course."
        )

    if score >= 50:
        return (
            "Good performance. "
            "The student has demonstrated "
            "a satisfactory understanding "
            "of the course."
        )

    if score >= 45:
        return (
            "Fair performance. "
            "Additional revision and practice "
            "are recommended."
        )

    if score >= 40:
        return (
            "Pass. The student should strengthen "
            "understanding of key course areas."
        )

    return (
        "Unsatisfactory performance. "
        "Additional academic support and "
        "focused revision are recommended."
    )


# ============================================================
# CLASS REMARKS
# ============================================================

def generate_class_remarks(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> list[dict[str, Any]]:

    performance = get_class_performance(
        db,
        university_id,
        course_offering_id,
    )

    remarks = []

    for student in performance["students"]:

        if not student["complete"]:
            remark = (
                "Assessment record is incomplete. "
                "Complete all required assessments "
                "before final evaluation."
            )
        else:
            remark = generate_student_remark(
                student["total_score"]
            )

        remarks.append(
            {
                "student_id":
                    student["student_id"],

                "matric_number":
                    student["matric_number"],

                "student_name":
                    student["student_name"],

                "total_score":
                    student["total_score"],

                "remark":
                    remark,
            }
        )

    return remarks


# ============================================================
# FULL LECTURER ANALYTICS REPORT
# ============================================================

def generate_lecturer_course_report(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> dict[str, Any]:

    performance = get_class_performance(
        db,
        university_id,
        course_offering_id,
    )

    distribution = get_score_distribution(
        db,
        university_id,
        course_offering_id,
    )

    at_risk = get_at_risk_students(
        db,
        university_id,
        course_offering_id,
    )

    remarks = generate_class_remarks(
        db,
        university_id,
        course_offering_id,
    )

    return {
        "course_offering_id":
            course_offering_id,

        "class_performance":
            performance,

        "score_distribution":
            distribution,

        "at_risk_students":
            at_risk,

        "automatic_remarks":
            remarks,

        "analytics_summary": {
            "average_score":
                performance["average_score"],

            "highest_score":
                performance["highest_score"],

            "lowest_score":
                performance["lowest_score"],

            "pass_rate":
                performance["pass_rate"],

            "fail_rate":
                performance["fail_rate"],

            "at_risk_count":
                len(at_risk),
        },
    }