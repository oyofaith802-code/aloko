from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.university_ai.models import (
    Assessment,
    Student,
    StudentCourse,
    StudentScore,
)


# ============================================================
# VALIDATION HELPERS
# ============================================================

VALID_ASSESSMENT_TYPES = {
    "ca",
    "test",
    "assignment",
    "exam",
    "practical",
    "project",
    "quiz",
    "other",
}


def validate_assessment_type(
    assessment_type: str,
) -> str:

    value = str(assessment_type).strip().lower()

    if value not in VALID_ASSESSMENT_TYPES:
        raise ValueError(
            f"Invalid assessment type: {assessment_type}"
        )

    return value


def validate_max_score(
    max_score: float,
) -> float:

    value = float(max_score)

    if value <= 0:
        raise ValueError(
            "Maximum score must be greater than zero."
        )

    return value


def validate_weight(
    weight: float | None,
) -> float | None:

    if weight is None:
        return None

    value = float(weight)

    if value < 0 or value > 100:
        raise ValueError(
            "Assessment weight must be between 0 and 100."
        )

    return value


def validate_score(
    score: float | None,
    max_score: float,
) -> float | None:

    if score is None:
        return None

    value = float(score)

    if value < 0:
        raise ValueError(
            "Score cannot be negative."
        )

    if value > max_score:
        raise ValueError(
            f"Score cannot exceed maximum score "
            f"of {max_score}."
        )

    return value


# ============================================================
# CREATE ASSESSMENT
# ============================================================

def create_assessment(
    db: Session,
    university_id: int,
    course_offering_id: int,
    title: str,
    assessment_type: str,
    max_score: float,
    created_by: int,
    weight: float | None = None,
    description: str | None = None,
    assessment_date=None,
) -> Assessment:

    if not title or not title.strip():
        raise ValueError(
            "Assessment title is required."
        )

    assessment_type = validate_assessment_type(
        assessment_type
    )

    max_score = validate_max_score(
        max_score
    )

    weight = validate_weight(weight)

    assessment = Assessment(
        university_id=university_id,
        course_offering_id=course_offering_id,
        title=title.strip(),
        assessment_type=assessment_type,
        description=description,
        max_score=max_score,
        weight=weight,
        assessment_date=assessment_date,
        is_published=False,
        status="active",
        created_by=created_by,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


# ============================================================
# UPDATE ASSESSMENT
# ============================================================

def update_assessment(
    db: Session,
    university_id: int,
    assessment_id: int,
    **updates,
) -> Assessment:

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.university_id == university_id,
        )
        .first()
    )

    if not assessment:
        raise ValueError(
            "Assessment not found."
        )

    if "title" in updates:
        title = updates["title"]

        if not title or not str(title).strip():
            raise ValueError(
                "Assessment title is required."
            )

        assessment.title = str(title).strip()

    if "assessment_type" in updates:
        assessment.assessment_type = (
            validate_assessment_type(
                updates["assessment_type"]
            )
        )

    if "max_score" in updates:
        assessment.max_score = (
            validate_max_score(
                updates["max_score"]
            )
        )

    if "weight" in updates:
        assessment.weight = (
            validate_weight(
                updates["weight"]
            )
        )

    if "description" in updates:
        assessment.description = (
            updates["description"]
        )

    if "assessment_date" in updates:
        assessment.assessment_date = (
            updates["assessment_date"]
        )

    db.commit()
    db.refresh(assessment)

    return assessment


# ============================================================
# DELETE / DEACTIVATE ASSESSMENT
# ============================================================

def deactivate_assessment(
    db: Session,
    university_id: int,
    assessment_id: int,
) -> Assessment:

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.university_id == university_id,
        )
        .first()
    )

    if not assessment:
        raise ValueError(
            "Assessment not found."
        )

    assessment.status = "inactive"

    db.commit()
    db.refresh(assessment)

    return assessment


# ============================================================
# LIST ASSESSMENTS
# ============================================================

def list_assessments(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> list[dict[str, Any]]:

    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.university_id == university_id,
            Assessment.course_offering_id
            == course_offering_id,
            Assessment.status == "active",
        )
        .order_by(
            Assessment.assessment_date,
            Assessment.id,
        )
        .all()
    )

    return [
        {
            "id": assessment.id,
            "title": assessment.title,
            "assessment_type":
                assessment.assessment_type,
            "description":
                assessment.description,
            "max_score":
                assessment.max_score,
            "weight":
                assessment.weight,
            "assessment_date":
                assessment.assessment_date,
            "is_published":
                assessment.is_published,
            "status":
                assessment.status,
        }
        for assessment in assessments
    ]


# ============================================================
# VALIDATE COURSE ASSESSMENTS
# ============================================================

def validate_course_assessments(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> dict[str, Any]:

    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.university_id == university_id,
            Assessment.course_offering_id
            == course_offering_id,
            Assessment.status == "active",
        )
        .all()
    )

    missing_weights = []
    total_weight = 0.0

    for assessment in assessments:

        if assessment.weight is None:
            missing_weights.append(
                {
                    "assessment_id":
                        assessment.id,
                    "title":
                        assessment.title,
                }
            )
            continue

        total_weight += float(
            assessment.weight
        )

    total_weight = round(
        total_weight,
        2,
    )

    errors = []

    if not assessments:
        errors.append(
            "No active assessments found."
        )

    if missing_weights:
        errors.append(
            "One or more assessments have no weight."
        )

    if assessments and abs(
        total_weight - 100.0
    ) > 0.01:
        errors.append(
            f"Assessment weights must total 100%. "
            f"Current total: {total_weight}%."
        )

    return {
        "valid": len(errors) == 0,
        "assessment_count":
            len(assessments),
        "total_weight":
            total_weight,
        "missing_weights":
            missing_weights,
        "errors":
            errors,
    }


# ============================================================
# ENTER / UPDATE STUDENT SCORE
# ============================================================

def save_student_score(
    db: Session,
    university_id: int,
    student_id: int,
    assessment_id: int,
    score: float | None,
    marked_by: int | None = None,
    is_absent: bool = False,
    lecturer_comment: str | None = None,
) -> StudentScore:

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.university_id == university_id,
            Assessment.status == "active",
        )
        .first()
    )

    if not assessment:
        raise ValueError(
            "Assessment not found."
        )

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id,
            Student.university_id == university_id,
            Student.status == "active",
        )
        .first()
    )

    if not student:
        raise ValueError(
            "Student not found."
        )

    enrollment = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.university_id
            == university_id,

            StudentCourse.student_id
            == student_id,

            StudentCourse.course_offering_id
            == assessment.course_offering_id,

            StudentCourse.enrollment_status
            == "enrolled",
        )
        .first()
    )

    if not enrollment:
        raise ValueError(
            "Student is not enrolled in this course."
        )

    if is_absent:
        validated_score = None
    else:
        validated_score = validate_score(
            score,
            assessment.max_score,
        )

    percentage = None

    if validated_score is not None:
        percentage = (
            validated_score
            / assessment.max_score
        ) * 100

        percentage = round(
            percentage,
            2,
        )

    existing = (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id
            == university_id,

            StudentScore.student_id
            == student_id,

            StudentScore.assessment_id
            == assessment_id,
        )
        .first()
    )

    if existing:

        existing.score = validated_score
        existing.percentage = percentage
        existing.is_absent = is_absent
        existing.status = (
            "absent"
            if is_absent
            else "marked"
        )
        existing.lecturer_comment = (
            lecturer_comment
        )
        existing.marked_by = marked_by

        from sqlalchemy.sql import func

        existing.marked_at = func.now()

        db.commit()
        db.refresh(existing)

        return existing

    student_score = StudentScore(
        university_id=university_id,
        student_id=student_id,
        assessment_id=assessment_id,
        course_offering_id=
            assessment.course_offering_id,
        score=validated_score,
        percentage=percentage,
        status=(
            "absent"
            if is_absent
            else "marked"
        ),
        is_absent=is_absent,
        lecturer_comment=lecturer_comment,
        marked_by=marked_by,
    )

    db.add(student_score)
    db.commit()
    db.refresh(student_score)

    return student_score


# ============================================================
# COURSE SCORE COMPLETION
# ============================================================

def get_score_completion(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> dict[str, Any]:

    students = (
        db.query(Student)
        .join(
            StudentCourse,
            StudentCourse.student_id
            == Student.id,
        )
        .filter(
            StudentCourse.university_id
            == university_id,

            StudentCourse.course_offering_id
            == course_offering_id,

            StudentCourse.enrollment_status
            == "enrolled",

            Student.university_id
            == university_id,

            Student.status == "active",
        )
        .all()
    )

    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.university_id
            == university_id,

            Assessment.course_offering_id
            == course_offering_id,

            Assessment.status == "active",
        )
        .all()
    )

    total_expected = (
        len(students)
        * len(assessments)
    )

    scores = (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id
            == university_id,

            StudentScore.course_offering_id
            == course_offering_id,
        )
        .all()
    )

    marked = sum(
        1
        for score in scores
        if score.status in (
            "marked",
            "absent",
        )
    )

    missing = max(
        total_expected - marked,
        0,
    )

    completion = 0.0

    if total_expected > 0:
        completion = (
            marked
            / total_expected
        ) * 100

    return {
        "course_offering_id":
            course_offering_id,

        "students":
            len(students),

        "assessments":
            len(assessments),

        "expected_scores":
            total_expected,

        "marked_scores":
            marked,

        "missing_scores":
            missing,

        "completion_percentage":
            round(completion, 2),

        "complete":
            missing == 0,
    }


# ============================================================
# MISSING SCORE REPORT
# ============================================================

def get_missing_scores(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> list[dict[str, Any]]:

    students = (
        db.query(Student)
        .join(
            StudentCourse,
            StudentCourse.student_id
            == Student.id,
        )
        .filter(
            StudentCourse.university_id
            == university_id,

            StudentCourse.course_offering_id
            == course_offering_id,

            StudentCourse.enrollment_status
            == "enrolled",

            Student.university_id
            == university_id,

            Student.status == "active",
        )
        .all()
    )

    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.university_id
            == university_id,

            Assessment.course_offering_id
            == course_offering_id,

            Assessment.status == "active",
        )
        .all()
    )

    scores = (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id
            == university_id,

            StudentScore.course_offering_id
            == course_offering_id,
        )
        .all()
    )

    score_map = {
        (
            score.student_id,
            score.assessment_id,
        ): score
        for score in scores
    }

    missing = []

    for student in students:

        for assessment in assessments:

            score = score_map.get(
                (
                    student.id,
                    assessment.id,
                )
            )

            if score is None:

                missing.append(
                    {
                        "student_id":
                            student.id,

                        "matric_number":
                            student.matric_number,

                        "student_name":
                            (
                                f"{student.first_name} "
                                f"{student.last_name}"
                            ),

                        "assessment_id":
                            assessment.id,

                        "assessment":
                            assessment.title,
                    }
                )

    return missing


# ============================================================
# COURSE SCORE COMPILATION
# ============================================================

def compile_course_scores(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> dict[str, Any]:

    validation = validate_course_assessments(
        db=db,
        university_id=university_id,
        course_offering_id=course_offering_id,
    )

    if not validation["valid"]:
        return {
            "success": False,
            "validation":
                validation,
            "students": [],
        }

    students = (
        db.query(Student)
        .join(
            StudentCourse,
            StudentCourse.student_id
            == Student.id,
        )
        .filter(
            StudentCourse.university_id
            == university_id,

            StudentCourse.course_offering_id
            == course_offering_id,

            StudentCourse.enrollment_status
            == "enrolled",

            Student.university_id
            == university_id,

            Student.status == "active",
        )
        .all()
    )

    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.university_id
            == university_id,

            Assessment.course_offering_id
            == course_offering_id,

            Assessment.status == "active",
        )
        .all()
    )

    scores = (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id
            == university_id,

            StudentScore.course_offering_id
            == course_offering_id,
        )
        .all()
    )

    score_map = {
        (
            score.student_id,
            score.assessment_id,
        ): score
        for score in scores
    }

    compiled_students = []

    for student in students:

        weighted_total = 0.0
        complete = True
        assessment_rows = []

        for assessment in assessments:

            score = score_map.get(
                (
                    student.id,
                    assessment.id,
                )
            )

            if score is None:
                complete = False

                assessment_rows.append(
                    {
                        "assessment_id":
                            assessment.id,
                        "title":
                            assessment.title,
                        "score":
                            None,
                        "percentage":
                            None,
                        "weight":
                            assessment.weight,
                        "weighted_score":
                            None,
                        "status":
                            "missing",
                    }
                )

                continue

            percentage = (
                score.percentage
                if score.percentage is not None
                else 0.0
            )

            weighted_score = (
                percentage
                * float(assessment.weight)
                / 100
            )

            weighted_total += weighted_score

            assessment_rows.append(
                {
                    "assessment_id":
                        assessment.id,

                    "title":
                        assessment.title,

                    "score":
                        score.score,

                    "percentage":
                        percentage,

                    "weight":
                        assessment.weight,

                    "weighted_score":
                        round(
                            weighted_score,
                            2,
                        ),

                    "status":
                        score.status,
                }
            )

        compiled_students.append(
            {
                "student_id":
                    student.id,

                "matric_number":
                    student.matric_number,

                "student_name":
                    (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    ),

                "complete":
                    complete,

                "total_score":
                    round(
                        weighted_total,
                        2,
                    ),

                "assessments":
                    assessment_rows,
            }
        )

    return {
        "success": True,

        "course_offering_id":
            course_offering_id,

        "students":
            compiled_students,

        "student_count":
            len(compiled_students),

        "complete_students":
            sum(
                1
                for student
                in compiled_students
                if student["complete"]
            ),

        "incomplete_students":
            sum(
                1
                for student
                in compiled_students
                if not student["complete"]
            ),

        "assessment_validation":
            validation,
    }