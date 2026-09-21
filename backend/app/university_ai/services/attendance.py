from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.university_ai.models.attendance import AttendanceRecord
from app.university_ai.models.people import Student
from app.university_ai.models.academic import (
    CourseOffering,
    StudentCourse,
)


VALID_ATTENDANCE_STATUSES = {
    "present",
    "absent",
    "late",
    "excused",
}


def validate_attendance_status(status: str) -> str:
    status = str(status).strip().lower()

    if status not in VALID_ATTENDANCE_STATUSES:
        raise ValueError(
            f"Invalid attendance status: {status}. "
            f"Allowed: {sorted(VALID_ATTENDANCE_STATUSES)}"
        )

    return status


def mark_attendance(
    db: Session,
    university_id: int,
    course_offering_id: int,
    student_id: int,
    attendance_date,
    status: str,
    marked_by: int,
    note: str = None,
):
    status = validate_attendance_status(status)

    student_course = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.university_id == university_id,
            StudentCourse.course_offering_id == course_offering_id,
            StudentCourse.student_id == student_id,
            StudentCourse.enrollment_status == "enrolled",
        )
        .first()
    )

    if not student_course:
        raise ValueError(
            "Student is not enrolled in this course offering."
        )

    if isinstance(attendance_date, date) and not isinstance(
        attendance_date, datetime
    ):
        attendance_date = datetime.combine(
            attendance_date,
            datetime.min.time()
        )

    existing = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.university_id == university_id,
            AttendanceRecord.course_offering_id == course_offering_id,
            AttendanceRecord.student_id == student_id,
            func.date(AttendanceRecord.attendance_date)
            == attendance_date.date(),
        )
        .first()
    )

    if existing:
        existing.status = status
        existing.note = note
        existing.marked_by = marked_by
        db.commit()
        db.refresh(existing)
        return existing

    record = AttendanceRecord(
        university_id=university_id,
        course_offering_id=course_offering_id,
        student_id=student_id,
        attendance_date=attendance_date,
        status=status,
        note=note,
        marked_by=marked_by,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def bulk_mark_attendance(
    db: Session,
    university_id: int,
    course_offering_id: int,
    attendance_date,
    records: list,
    marked_by: int,
):
    results = []

    for item in records:
        student_id = item.get("student_id")
        status = item.get("status", "present")
        note = item.get("note")

        result = mark_attendance(
            db=db,
            university_id=university_id,
            course_offering_id=course_offering_id,
            student_id=student_id,
            attendance_date=attendance_date,
            status=status,
            marked_by=marked_by,
            note=note,
        )

        results.append(result)

    return results


def update_attendance(
    db: Session,
    attendance_id: int,
    status: str = None,
    note: str = None,
):
    record = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.id == attendance_id)
        .first()
    )

    if not record:
        raise ValueError("Attendance record not found.")

    if status is not None:
        record.status = validate_attendance_status(status)

    if note is not None:
        record.note = note

    db.commit()
    db.refresh(record)

    return record


def get_student_attendance_history(
    db: Session,
    university_id: int,
    student_id: int,
    course_offering_id: int = None,
):
    query = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.university_id == university_id,
            AttendanceRecord.student_id == student_id,
        )
    )

    if course_offering_id is not None:
        query = query.filter(
            AttendanceRecord.course_offering_id == course_offering_id
        )

    return (
        query
        .order_by(AttendanceRecord.attendance_date.desc())
        .all()
    )


def calculate_attendance_percentage(
    records: list,
):
    if not records:
        return 0.0

    counted = [
        record
        for record in records
        if record.status != "excused"
    ]

    if not counted:
        return 100.0

    attended = sum(
        1
        for record in counted
        if record.status in {"present", "late"}
    )

    return round(
        (attended / len(counted)) * 100,
        2,
    )


def get_course_attendance_summary(
    db: Session,
    university_id: int,
    course_offering_id: int,
):
    students = (
        db.query(Student)
        .join(
            StudentCourse,
            StudentCourse.student_id == Student.id
        )
        .filter(
            StudentCourse.university_id == university_id,
            StudentCourse.course_offering_id == course_offering_id,
            StudentCourse.enrollment_status == "enrolled",
        )
        .all()
    )

    summary = []

    for student in students:
        records = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.university_id == university_id,
                AttendanceRecord.course_offering_id
                == course_offering_id,
                AttendanceRecord.student_id == student.id,
            )
            .order_by(AttendanceRecord.attendance_date)
            .all()
        )

        percentage = calculate_attendance_percentage(records)

        summary.append(
            {
                "student_id": student.id,
                "matric_number": student.matric_number,
                "name": (
                    f"{student.first_name} "
                    f"{student.middle_name or ''} "
                    f"{student.last_name}"
                ).strip(),
                "total_records": len(records),
                "present": sum(
                    1 for r in records if r.status == "present"
                ),
                "absent": sum(
                    1 for r in records if r.status == "absent"
                ),
                "late": sum(
                    1 for r in records if r.status == "late"
                ),
                "excused": sum(
                    1 for r in records if r.status == "excused"
                ),
                "attendance_percentage": percentage,
            }
        )

    return summary


def get_low_attendance_students(
    db: Session,
    university_id: int,
    course_offering_id: int,
    threshold: float = 75.0,
):
    summary = get_course_attendance_summary(
        db,
        university_id,
        course_offering_id,
    )

    return [
        student
        for student in summary
        if student["attendance_percentage"] < threshold
    ]


def generate_lecturer_attendance_report(
    db: Session,
    university_id: int,
    course_offering_id: int,
    low_attendance_threshold: float = 75.0,
):
    summary = get_course_attendance_summary(
        db,
        university_id,
        course_offering_id,
    )

    low_attendance = [
        item
        for item in summary
        if item["attendance_percentage"]
        < low_attendance_threshold
    ]

    total_students = len(summary)

    if total_students:
        average_attendance = round(
            sum(
                item["attendance_percentage"]
                for item in summary
            ) / total_students,
            2,
        )
    else:
        average_attendance = 0.0

    return {
        "course_offering_id": course_offering_id,
        "total_students": total_students,
        "average_attendance": average_attendance,
        "low_attendance_threshold": low_attendance_threshold,
        "low_attendance_students": low_attendance,
        "students": summary,
    }