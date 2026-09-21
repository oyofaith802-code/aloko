from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.university_ai.models.people import Student
from app.university_ai.models.assessment import Assessment, StudentScore


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def normalize_column_name(value: Any) -> str:
    if value is None:
        return ""

    value = str(value).strip().lower()
    value = value.replace("_", " ")
    value = value.replace("-", " ")
    value = value.replace(".", "")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_matric(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None

    value = str(value).strip().upper()
    value = re.sub(r"\s+", "", value)

    return value or None


# ============================================================
# FILE READER
# ============================================================

def read_score_file(
    file_bytes: bytes,
    filename: str,
) -> pd.DataFrame:
    """Read CSV/XLSX/XLS score sheets."""

    if not file_bytes:
        raise ValueError("Uploaded score file is empty.")

    filename_lower = filename.lower().strip()

    try:
        if filename_lower.endswith(".csv"):
            return pd.read_csv(
                io.BytesIO(file_bytes),
                dtype=str,
            )

        if filename_lower.endswith(".xlsx"):
            return pd.read_excel(
                io.BytesIO(file_bytes),
                dtype=str,
                engine="openpyxl",
            )

        if filename_lower.endswith(".xls"):
            return pd.read_excel(
                io.BytesIO(file_bytes),
                dtype=str,
            )

    except Exception as exc:
        raise ValueError(
            f"Unable to read score file: {exc}"
        ) from exc

    raise ValueError(
        "Unsupported file type. Upload CSV, XLSX, or XLS."
    )


# ============================================================
# MATRIC COLUMN DETECTION
# ============================================================

MATRIC_ALIASES = {
    "matric",
    "matric no",
    "matric number",
    "matric no.",
    "matric_number",
    "registration number",
    "registration no",
    "registration no.",
    "reg no",
    "reg no.",
    "student id",
    "student number",
    "student_id",
}


def detect_matric_column(
    df: pd.DataFrame,
) -> str | None:

    normalized_aliases = {
        normalize_column_name(alias)
        for alias in MATRIC_ALIASES
    }

    for column in df.columns:
        normalized = normalize_column_name(column)

        if normalized in normalized_aliases:
            return column

    return None


# ============================================================
# ASSESSMENT COLUMN DETECTION
# ============================================================

def detect_assessment_columns(
    df: pd.DataFrame,
    matric_column: str,
) -> list[str]:

    ignored_columns = {
        "name",
        "student name",
        "first name",
        "last name",
        "surname",
        "department",
        "dept",
        "level",
        "faculty",
        "programme",
        "program",
        "phone",
    }

    columns = []

    for column in df.columns:

        if column == matric_column:
            continue

        normalized = normalize_column_name(column)

        if not normalized:
            continue

        if normalized in ignored_columns:
            continue

        columns.append(column)

    return columns


# ============================================================
# SCORE CONVERSION
# ============================================================

def parse_score(value: Any) -> float | None:

    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    value = value.replace("%", "").strip()

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


# ============================================================
# DUPLICATE MATRIC DETECTION
# ============================================================

def detect_duplicate_matric(
    df: pd.DataFrame,
    matric_column: str,
) -> list[dict[str, Any]]:

    seen: dict[str, int] = {}
    duplicates = []

    for index, value in enumerate(
        df[matric_column],
        start=2,
    ):

        matric = normalize_matric(value)

        if not matric:
            continue

        if matric in seen:

            duplicates.append(
                {
                    "row": index,
                    "matric_number": matric,
                    "first_row": seen[matric],
                }
            )

        else:
            seen[matric] = index

    return duplicates


# ============================================================
# FIND STUDENTS
# ============================================================

def find_students(
    db: Session,
    university_id: int,
    matric_numbers: list[str],
) -> dict[str, Student]:

    if not matric_numbers:
        return {}

    students = (
        db.query(Student)
        .filter(
            Student.university_id == university_id,
            Student.matric_number.in_(matric_numbers),
        )
        .all()
    )

    return {
        student.matric_number.upper(): student
        for student in students
    }


# ============================================================
# FIND ASSESSMENTS
# ============================================================

def find_assessments(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> list[Assessment]:

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


# ============================================================
# MATCH ASSESSMENT
# ============================================================

def match_assessment_column(
    column_name: str,
    assessments: list[Assessment],
) -> Assessment | None:

    normalized_column = normalize_column_name(
        column_name
    )

    for assessment in assessments:

        normalized_title = normalize_column_name(
            assessment.title
        )

        if normalized_column == normalized_title:
            return assessment

        if normalized_column in normalized_title:
            return assessment

        if normalized_title in normalized_column:
            return assessment

    return None


# ============================================================
# SCORE VALIDATION
# ============================================================

def validate_score(
    score: float | None,
    max_score: float,
) -> str | None:

    if score is None:
        return "Missing score."

    if score < 0:
        return "Score cannot be negative."

    if score > max_score:
        return (
            f"Score {score} exceeds maximum "
            f"score {max_score}."
        )

    return None


# ============================================================
# PREVIEW IMPORT
# ============================================================

def preview_score_import(
    db: Session,
    university_id: int,
    course_offering_id: int,
    file_bytes: bytes,
    filename: str,
) -> dict[str, Any]:

    df = read_score_file(
        file_bytes,
        filename,
    )

    if df.empty:
        raise ValueError(
            "The uploaded score sheet contains no records."
        )

    matric_column = detect_matric_column(df)

    if not matric_column:
        raise ValueError(
            "Could not identify the matric/student number column."
        )

    assessment_columns = detect_assessment_columns(
        df,
        matric_column,
    )

    if not assessment_columns:
        raise ValueError(
            "No assessment columns were detected."
        )

    assessments = find_assessments(
        db,
        university_id,
        course_offering_id,
    )

    if not assessments:
        raise ValueError(
            "No assessments exist for this course offering."
        )

    # --------------------------------------------------------
    # Duplicate matric numbers
    # --------------------------------------------------------

    duplicates = detect_duplicate_matric(
        df,
        matric_column,
    )

    # --------------------------------------------------------
    # Student matching
    # --------------------------------------------------------

    matric_numbers = []

    for value in df[matric_column]:

        matric = normalize_matric(value)

        if matric:
            matric_numbers.append(matric)

    students = find_students(
        db,
        university_id,
        matric_numbers,
    )

    unmatched_students = []

    for index, value in enumerate(
        df[matric_column],
        start=2,
    ):

        matric = normalize_matric(value)

        if not matric:

            unmatched_students.append(
                {
                    "row": index,
                    "matric_number": None,
                    "reason": "Missing matric number.",
                }
            )

        elif matric not in students:

            unmatched_students.append(
                {
                    "row": index,
                    "matric_number": matric,
                    "reason": "Student not found.",
                }
            )

    # --------------------------------------------------------
    # Assessment matching
    # --------------------------------------------------------

    matched_assessments = {}
    unmatched_assessment_columns = []

    for column in assessment_columns:

        assessment = match_assessment_column(
            column,
            assessments,
        )

        if assessment:

            matched_assessments[column] = assessment

        else:

            unmatched_assessment_columns.append(
                column
            )

    # --------------------------------------------------------
    # Score validation
    # --------------------------------------------------------

    score_errors = []
    score_rows = []

    for index, row in df.iterrows():

        source_row = index + 2

        matric = normalize_matric(
            row[matric_column]
        )

        for column, assessment in matched_assessments.items():

            score = parse_score(
                row[column]
            )

            error = validate_score(
                score,
                assessment.max_score,
            )

            if error:

                score_errors.append(
                    {
                        "row": source_row,
                        "matric_number": matric,
                        "assessment": assessment.title,
                        "score": score,
                        "max_score": assessment.max_score,
                        "message": error,
                    }
                )

            percentage = None

            if score is not None and assessment.max_score:
                percentage = (
                    score / assessment.max_score
                ) * 100

            score_rows.append(
                {
                    "source_row": source_row,
                    "matric_number": matric,
                    "student_id": (
                        students[matric].id
                        if matric in students
                        else None
                    ),
                    "assessment_id": assessment.id,
                    "course_offering_id":
                        course_offering_id,
                    "assessment": assessment.title,
                    "score": score,
                    "max_score": assessment.max_score,
                    "percentage": percentage,
                }
            )

    # --------------------------------------------------------
    # Existing score detection
    # --------------------------------------------------------

    existing_scores = []

    for item in score_rows:

        if not item["student_id"]:
            continue

        existing = (
            db.query(StudentScore)
            .filter(
                StudentScore.university_id
                == university_id,
                StudentScore.student_id
                == item["student_id"],
                StudentScore.assessment_id
                == item["assessment_id"],
                StudentScore.course_offering_id
                == course_offering_id,
            )
            .first()
        )

        if existing:

            existing_scores.append(
                {
                    **item,
                    "existing_score": existing.score,
                }
            )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    valid = (
        len(duplicates) == 0
        and len(unmatched_students) == 0
        and len(unmatched_assessment_columns) == 0
        and len(score_errors) == 0
    )

    return {
        "filename": filename,
        "total_rows": len(df),

        "matric_column": matric_column,

        "assessment_columns":
            assessment_columns,

        "matched_assessments": [
            {
                "column": column,
                "assessment_id": assessment.id,
                "title": assessment.title,
                "max_score": assessment.max_score,
            }
            for column, assessment
            in matched_assessments.items()
        ],

        "unmatched_assessment_columns":
            unmatched_assessment_columns,

        "duplicate_students":
            duplicates,

        "unmatched_students":
            unmatched_students,

        "score_errors":
            score_errors,

        "existing_scores":
            existing_scores,

        "score_rows":
            score_rows,

        "valid":
            valid,
    }


# ============================================================
# IMPORT SCORES
# ============================================================

def import_scores(
    db: Session,
    university_id: int,
    course_offering_id: int,
    preview: dict[str, Any],
    overwrite_existing: bool = False,
) -> dict[str, Any]:

    if not preview["valid"]:

        return {
            "success": False,
            "message": (
                "Score import blocked because "
                "validation errors exist."
            ),
            "created": 0,
            "updated": 0,
        }

    created = 0
    updated = 0

    try:

        for item in preview["score_rows"]:

            student_id = item["student_id"]

            if not student_id:
                continue

            score = item["score"]

            if score is None:
                continue

            percentage = item["percentage"]

            existing = (
                db.query(StudentScore)
                .filter(
                    StudentScore.university_id
                    == university_id,
                    StudentScore.student_id
                    == student_id,
                    StudentScore.assessment_id
                    == item["assessment_id"],
                    StudentScore.course_offering_id
                    == course_offering_id,
                )
                .first()
            )

            if existing:

                if overwrite_existing:

                    existing.score = score
                    existing.percentage = percentage
                    existing.status = "marked"

                    updated += 1

                continue

            student_score = StudentScore(
                university_id=university_id,
                student_id=student_id,
                assessment_id=item["assessment_id"],
                course_offering_id=course_offering_id,
                score=score,
                percentage=percentage,
                status="marked",
            )

            db.add(student_score)

            created += 1

        db.commit()

        return {
            "success": True,
            "message": (
                "Score sheet imported successfully."
            ),
            "created": created,
            "updated": updated,
            "total_processed":
                created + updated,
        }

    except Exception as exc:

        db.rollback()

        return {
            "success": False,
            "message":
                f"Score import failed: {exc}",
            "created": 0,
            "updated": 0,
            "total_processed": 0,
        }


# ============================================================
# COMPLETE SCORE IMPORT PIPELINE
# ============================================================

def process_score_import(
    db: Session,
    university_id: int,
    course_offering_id: int,
    file_bytes: bytes,
    filename: str,
    commit: bool = False,
    overwrite_existing: bool = False,
) -> dict[str, Any]:

    preview = preview_score_import(
        db=db,
        university_id=university_id,
        course_offering_id=course_offering_id,
        file_bytes=file_bytes,
        filename=filename,
    )

    if not commit:

        return {
            "success": preview["valid"],
            "mode": "preview",
            **preview,
        }

    if not preview["valid"]:

        return {
            "success": False,
            "mode": "commit",
            "message": (
                "Import blocked. Fix validation "
                "errors before importing."
            ),
            **preview,
        }

    result = import_scores(
        db=db,
        university_id=university_id,
        course_offering_id=course_offering_id,
        preview=preview,
        overwrite_existing=overwrite_existing,
    )

    return {
        **result,
        "mode": "commit",
    }