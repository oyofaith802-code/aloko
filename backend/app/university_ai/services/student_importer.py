from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.university_ai.models.people import Student


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {
    "matric_number": [
        "matric",
        "matric no",
        "matric no.",
        "matric number",
        "matric_number",
        "matricnumber",
        "registration number",
        "registration no",
        "registration no.",
        "reg no",
        "reg no.",
        "student id",
        "student_id",
        "student number",
    ],
    "first_name": [
        "first name",
        "firstname",
        "first_name",
        "given name",
    ],
    "middle_name": [
        "middle name",
        "middlename",
        "middle_name",
    ],
    "last_name": [
        "last name",
        "lastname",
        "last_name",
        "surname",
        "family name",
    ],
    "department": [
        "department",
        "dept",
        "department name",
    ],
    "level": [
        "level",
        "class level",
        "student level",
        "year",
    ],
    "faculty": [
        "faculty",
        "faculty name",
    ],
    "programme": [
        "programme",
        "program",
        "programme name",
        "program name",
        "course of study",
    ],
    "entry_year": [
        "entry year",
        "entry_year",
        "admission year",
        "year admitted",
    ],
    "graduation_year": [
        "graduation year",
        "graduation_year",
        "year of graduation",
    ],
    "phone": [
        "phone",
        "phone number",
        "telephone",
        "mobile",
        "mobile number",
    ],
}


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_column_name(value: Any) -> str:
    """
    Converts arbitrary Excel/CSV column names into a
    predictable comparison format.
    """
    if value is None:
        return ""

    value = str(value).strip().lower()

    value = value.replace("_", " ")
    value = value.replace("-", " ")
    value = value.replace(".", "")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_text(value: Any) -> str | None:
    """
    Normalize cell values while preserving useful text.
    """
    if value is None:
        return None

    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def normalize_matric(value: Any) -> str | None:
    """
    Normalize matric/student ID values.

    Important:
    Matric numbers are kept as strings so values such as
    21/1234 or 00123 are not accidentally converted to numbers.
    """
    value = normalize_text(value)

    if value is None:
        return None

    value = value.strip().upper()

    # Remove accidental surrounding spaces
    value = re.sub(r"\s+", "", value)

    return value


def normalize_level(value: Any) -> str | None:
    value = normalize_text(value)

    if value is None:
        return None

    value = value.upper().strip()

    # Convert common numeric Excel values such as 300.0 -> 300
    if value.endswith(".0"):
        value = value[:-2]

    return value


def normalize_year(value: Any) -> int | None:
    value = normalize_text(value)

    if value is None:
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


# ============================================================
# FILE READING
# ============================================================

def read_student_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    Read CSV or Excel student list into a DataFrame.
    """

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    filename_lower = filename.lower().strip()

    try:
        if filename_lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_bytes), dtype=str)

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
            f"Unable to read the uploaded file: {exc}"
        ) from exc

    raise ValueError(
        "Unsupported file type. Please upload CSV, XLSX, or XLS."
    )


# ============================================================
# COLUMN DETECTION
# ============================================================

def detect_columns(df: pd.DataFrame) -> dict[str, str]:
    """
    Automatically map uploaded column names to our internal fields.
    """

    normalized_columns = {
        column: normalize_column_name(column)
        for column in df.columns
    }

    detected: dict[str, str] = {}

    for internal_name, aliases in COLUMN_ALIASES.items():
        normalized_aliases = {
            normalize_column_name(alias)
            for alias in aliases
        }

        for original_column, normalized_column in normalized_columns.items():
            if normalized_column in normalized_aliases:
                detected[internal_name] = original_column
                break

    return detected


# ============================================================
# ROW EXTRACTION
# ============================================================

def extract_student_rows(
    df: pd.DataFrame,
    detected_columns: dict[str, str],
) -> list[dict[str, Any]]:
    """
    Convert raw DataFrame rows into normalized student dictionaries.
    """

    students = []

    for index, row in df.iterrows():
        excel_row_number = index + 2

        matric = normalize_matric(
            row.get(detected_columns.get("matric_number"))
        )

        first_name = normalize_text(
            row.get(detected_columns.get("first_name"))
        )

        middle_name = normalize_text(
            row.get(detected_columns.get("middle_name"))
        )

        last_name = normalize_text(
            row.get(detected_columns.get("last_name"))
        )

        department = normalize_text(
            row.get(detected_columns.get("department"))
        )

        level = normalize_level(
            row.get(detected_columns.get("level"))
        )

        faculty = normalize_text(
            row.get(detected_columns.get("faculty"))
        )

        programme = normalize_text(
            row.get(detected_columns.get("programme"))
        )

        entry_year = normalize_year(
            row.get(detected_columns.get("entry_year"))
        )

        graduation_year = normalize_year(
            row.get(detected_columns.get("graduation_year"))
        )

        phone = normalize_text(
            row.get(detected_columns.get("phone"))
        )

        # Completely empty row
        if not any(
            [
                matric,
                first_name,
                middle_name,
                last_name,
                department,
                level,
                faculty,
                programme,
            ]
        ):
            continue

        students.append(
            {
                "source_row": excel_row_number,
                "matric_number": matric,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "department": department,
                "level": level,
                "faculty": faculty,
                "programme": programme,
                "entry_year": entry_year,
                "graduation_year": graduation_year,
                "phone": phone,
            }
        )

    return students


# ============================================================
# VALIDATION
# ============================================================

def validate_student_rows(
    students: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate imported students without writing anything
    to the database.
    """

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    seen_matric: dict[str, int] = {}

    for student in students:
        row = student["source_row"]
        matric = student["matric_number"]

        # ----------------------------------------------------
        # Required matric
        # ----------------------------------------------------

        if not matric:
            errors.append(
                {
                    "row": row,
                    "field": "matric_number",
                    "message": "Missing matric/student number.",
                }
            )

        else:
            if matric in seen_matric:
                errors.append(
                    {
                        "row": row,
                        "field": "matric_number",
                        "message": (
                            f"Duplicate matric number '{matric}'. "
                            f"First appeared on row {seen_matric[matric]}."
                        ),
                    }
                )
            else:
                seen_matric[matric] = row

        # ----------------------------------------------------
        # Required first name
        # ----------------------------------------------------

        if not student["first_name"]:
            errors.append(
                {
                    "row": row,
                    "field": "first_name",
                    "message": "Missing first name.",
                }
            )

        # ----------------------------------------------------
        # Required last name
        # ----------------------------------------------------

        if not student["last_name"]:
            errors.append(
                {
                    "row": row,
                    "field": "last_name",
                    "message": "Missing last name/surname.",
                }
            )

        # ----------------------------------------------------
        # Optional fields
        # ----------------------------------------------------

        if not student["department"]:
            warnings.append(
                {
                    "row": row,
                    "field": "department",
                    "message": "Department was not provided.",
                }
            )

        if not student["level"]:
            warnings.append(
                {
                    "row": row,
                    "field": "level",
                    "message": "Level was not provided.",
                }
            )

        if student["entry_year"] is not None:
            if not 1900 <= student["entry_year"] <= 2200:
                errors.append(
                    {
                        "row": row,
                        "field": "entry_year",
                        "message": "Invalid entry year.",
                    }
                )

        if student["graduation_year"] is not None:
            if not 1900 <= student["graduation_year"] <= 2200:
                errors.append(
                    {
                        "row": row,
                        "field": "graduation_year",
                        "message": "Invalid graduation year.",
                    }
                )

    return {
        "valid": len(errors) == 0,
        "total_rows": len(students),
        "valid_rows": len(students) - len(
            {
                error["row"]
                for error in errors
            }
        ),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


# ============================================================
# DATABASE MATCHING
# ============================================================

def find_existing_students(
    db: Session,
    university_id: int,
    matric_numbers: list[str],
) -> dict[str, Student]:
    """
    Find existing students by matric number.
    """

    if not matric_numbers:
        return {}

    rows = (
        db.query(Student)
        .filter(
            Student.university_id == university_id,
            Student.matric_number.in_(matric_numbers),
        )
        .all()
    )

    return {
        student.matric_number.upper(): student
        for student in rows
    }


# ============================================================
# PREVIEW
# ============================================================

def preview_student_import(
    db: Session,
    university_id: int,
    file_bytes: bytes,
    filename: str,
) -> dict[str, Any]:
    """
    Complete import preview.

    IMPORTANT:
    This function DOES NOT write to the database.
    """

    df = read_student_file(file_bytes, filename)

    if df.empty:
        raise ValueError("The uploaded file contains no student records.")

    detected_columns = detect_columns(df)

    if "matric_number" not in detected_columns:
        raise ValueError(
            "Could not identify a matric/student number column."
        )

    if "first_name" not in detected_columns:
        raise ValueError(
            "Could not identify a first name column."
        )

    if "last_name" not in detected_columns:
        raise ValueError(
            "Could not identify a last name/surname column."
        )

    students = extract_student_rows(
        df,
        detected_columns,
    )

    validation = validate_student_rows(students)

    matric_numbers = [
        student["matric_number"]
        for student in students
        if student["matric_number"]
    ]

    existing_students = find_existing_students(
        db,
        university_id,
        matric_numbers,
    )

    new_students = []
    existing_records = []

    for student in students:
        matric = student["matric_number"]

        if matric and matric in existing_students:
            existing_records.append(student)
        else:
            new_students.append(student)

    return {
        "filename": filename,
        "detected_columns": detected_columns,
        "students": students,
        "validation": validation,
        "database": {
            "new_students": len(new_students),
            "existing_students": len(existing_records),
        },
        "new_student_rows": new_students,
        "existing_student_rows": existing_records,
    }


# ============================================================
# DATABASE IMPORT
# ============================================================

def import_students(
    db: Session,
    university_id: int,
    students: list[dict[str, Any]],
    update_existing: bool = True,
) -> dict[str, Any]:
    """
    Commit validated student records to the database.

    Lecturer/admin should preview first.

    Existing records can optionally be updated.
    """

    validation = validate_student_rows(students)

    if not validation["valid"]:
        return {
            "success": False,
            "message": "Import blocked because validation errors exist.",
            "validation": validation,
            "created": 0,
            "updated": 0,
        }

    matric_numbers = [
        student["matric_number"]
        for student in students
        if student["matric_number"]
    ]

    existing_students = find_existing_students(
        db,
        university_id,
        matric_numbers,
    )

    created = 0
    updated = 0

    imported_students = []

    try:
        for data in students:
            matric = data["matric_number"]

            if not matric:
                continue

            existing = existing_students.get(matric)

            if existing:
                if update_existing:
                    existing.first_name = data["first_name"]
                    existing.middle_name = data["middle_name"]
                    existing.last_name = data["last_name"]

                    if data["level"] is not None:
                        existing.level = data["level"]

                    if data["entry_year"] is not None:
                        existing.entry_year = data["entry_year"]

                    if data["graduation_year"] is not None:
                        existing.graduation_year = data[
                            "graduation_year"
                        ]

                    if data["phone"] is not None:
                        existing.phone = data["phone"]

                    updated += 1

                imported_students.append(existing)

                continue

            student = Student(
                user_id=None,
                university_id=university_id,
                matric_number=matric,
                first_name=data["first_name"],
                middle_name=data["middle_name"],
                last_name=data["last_name"],
                level=data["level"],
                entry_year=data["entry_year"],
                graduation_year=data["graduation_year"],
                phone=data["phone"],
                status="active",
            )

            db.add(student)

            created += 1
            imported_students.append(student)

        db.commit()

        return {
            "success": True,
            "message": "Students imported successfully.",
            "created": created,
            "updated": updated,
            "total_processed": len(imported_students),
        }

    except Exception as exc:
        db.rollback()

        return {
            "success": False,
            "message": f"Student import failed: {exc}",
            "created": 0,
            "updated": 0,
            "total_processed": 0,
        }


# ============================================================
# COMPLETE IMPORT PIPELINE
# ============================================================

def process_student_import(
    db: Session,
    university_id: int,
    file_bytes: bytes,
    filename: str,
    commit: bool = False,
    update_existing: bool = True,
) -> dict[str, Any]:
    """
    Main entry point.

    commit=False:
        Preview and validate only.

    commit=True:
        Import validated students into PostgreSQL.
    """

    preview = preview_student_import(
        db=db,
        university_id=university_id,
        file_bytes=file_bytes,
        filename=filename,
    )

    if not commit:
        return {
            "success": preview["validation"]["valid"],
            "mode": "preview",
            **preview,
        }

    if not preview["validation"]["valid"]:
        return {
            "success": False,
            "mode": "commit",
            "message": (
                "Import blocked. Fix validation errors "
                "before importing."
            ),
            **preview,
        }

    result = import_students(
        db=db,
        university_id=university_id,
        students=preview["students"],
        update_existing=update_existing,
    )

    return {
        **result,
        "mode": "commit",
        "validation": preview["validation"],
        "detected_columns": preview["detected_columns"],
    }