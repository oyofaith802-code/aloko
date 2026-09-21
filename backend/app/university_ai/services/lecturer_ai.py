from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.university_ai.models import (
    Lecturer,
    LecturerCourse,
    CourseOffering,
    Assessment,
    StudentCourse,
    Student,
    StudentScore,
    ResultSheet,
)


# ============================================================
# LECTURER PROFILE
# ============================================================

def get_lecturer_profile(
    db: Session,
    university_id: int,
    lecturer_id: int,
) -> dict[str, Any]:

    lecturer = (
        db.query(Lecturer)
        .filter(
            Lecturer.id == lecturer_id,
            Lecturer.university_id == university_id,
        )
        .first()
    )

    if not lecturer:
        raise ValueError("Lecturer not found.")

    return {
        "id": lecturer.id,
        "user_id": lecturer.user_id,
        "university_id": lecturer.university_id,
        "staff_id": lecturer.staff_id,
        "first_name": lecturer.first_name,
        "middle_name": lecturer.middle_name,
        "last_name": lecturer.last_name,
        "title": lecturer.title,
        "academic_rank": lecturer.academic_rank,
        "specialization": lecturer.specialization,
        "faculty_id": lecturer.faculty_id,
        "department_id": lecturer.department_id,
        "is_department_head": lecturer.is_department_head,
        "status": lecturer.status,
    }


# ============================================================
# ASSIGNED COURSES
# ============================================================

def get_lecturer_courses(
    db: Session,
    university_id: int,
    lecturer_id: int,
) -> list[dict[str, Any]]:

    rows = (
        db.query(
            LecturerCourse,
            CourseOffering,
        )
        .join(
            CourseOffering,
            LecturerCourse.course_offering_id
            == CourseOffering.id,
        )
        .filter(
            LecturerCourse.university_id == university_id,
            LecturerCourse.lecturer_id == lecturer_id,
            LecturerCourse.status == "active",
            CourseOffering.status == "active",
        )
        .all()
    )

    courses = []

    for lecturer_course, offering in rows:

        courses.append(
            {
                "lecturer_course_id":
                    lecturer_course.id,

                "course_offering_id":
                    offering.id,

                "course_id":
                    offering.course_id,

                "class_id":
                    offering.class_id,

                "academic_session_id":
                    offering.academic_session_id,

                "semester_id":
                    offering.semester_id,

                "level":
                    offering.level,

                "section":
                    offering.section,

                "role":
                    lecturer_course.role,

                "can_manage_students":
                    lecturer_course.can_manage_students,

                "can_manage_assessments":
                    lecturer_course.can_manage_assessments,

                "can_manage_results":
                    lecturer_course.can_manage_results,
            }
        )

    return courses


# ============================================================
# COURSE STUDENTS
# ============================================================

def get_course_students(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> list[dict[str, Any]]:

    rows = (
        db.query(StudentCourse, Student)
        .join(
            Student,
            StudentCourse.student_id == Student.id,
        )
        .filter(
            StudentCourse.university_id == university_id,
            StudentCourse.course_offering_id
            == course_offering_id,
            StudentCourse.enrollment_status == "enrolled",
            Student.status == "active",
        )
        .all()
    )

    students = []

    for enrollment, student in rows:

        students.append(
            {
                "student_id": student.id,
                "matric_number":
                    student.matric_number,
                "first_name":
                    student.first_name,
                "middle_name":
                    student.middle_name,
                "last_name":
                    student.last_name,
                "level":
                    student.level,
                "enrollment_status":
                    enrollment.enrollment_status,
            }
        )

    return students


# ============================================================
# ASSESSMENTS
# ============================================================

def get_course_assessments_for_lecturer(
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
        .order_by(Assessment.assessment_date, Assessment.id)
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
# COURSE SCORE SUMMARY
# ============================================================

def get_course_score_summary(
    db: Session,
    university_id: int,
    course_offering_id: int,
) -> dict[str, Any]:

    students = get_course_students(
        db=db,
        university_id=university_id,
        course_offering_id=course_offering_id,
    )

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

    scores = (
        db.query(StudentScore)
        .filter(
            StudentScore.university_id == university_id,
            StudentScore.course_offering_id
            == course_offering_id,
        )
        .all()
    )

    score_map = {}

    for score in scores:
        score_map.setdefault(
            score.student_id,
            {}
        )[score.assessment_id] = score

    student_rows = []

    for student in students:

        student_scores = score_map.get(
            student["student_id"],
            {},
        )

        assessment_rows = []

        for assessment in assessments:

            score = student_scores.get(
                assessment.id
            )

            assessment_rows.append(
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
                        score.percentage
                        if score
                        else None,

                    "is_absent":
                        score.is_absent
                        if score
                        else False,

                    "status":
                        score.status
                        if score
                        else "missing",
                }
            )

        student_rows.append(
            {
                **student,
                "assessments":
                    assessment_rows,
            }
        )

    return {
        "course_offering_id":
            course_offering_id,

        "total_students":
            len(students),

        "total_assessments":
            len(assessments),

        "students":
            student_rows,
    }


# ============================================================
# LECTURER DASHBOARD
# ============================================================

def get_lecturer_dashboard(
    db: Session,
    university_id: int,
    lecturer_id: int,
) -> dict[str, Any]:

    lecturer = get_lecturer_profile(
        db=db,
        university_id=university_id,
        lecturer_id=lecturer_id,
    )

    courses = get_lecturer_courses(
        db=db,
        university_id=university_id,
        lecturer_id=lecturer_id,
    )

    total_students = 0
    total_assessments = 0

    course_summaries = []

    for course in courses:

        students = get_course_students(
            db=db,
            university_id=university_id,
            course_offering_id=
                course["course_offering_id"],
        )

        assessments = get_course_assessments_for_lecturer(
            db=db,
            university_id=university_id,
            course_offering_id=
                course["course_offering_id"],
        )

        total_students += len(students)
        total_assessments += len(assessments)

        course_summaries.append(
            {
                **course,
                "student_count":
                    len(students),
                "assessment_count":
                    len(assessments),
            }
        )

    return {
        "lecturer": lecturer,

        "summary": {
            "total_courses":
                len(courses),

            "total_students":
                total_students,

            "total_assessments":
                total_assessments,
        },

        "courses":
            course_summaries,
    }