from pathlib import Path
from io import BytesIO, StringIO
import csv

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Body,
    UploadFile,
    File,
    Form,
    Query,
)
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User

from app.university_ai.models.people import Lecturer, Student
from app.university_ai.models.student_invitation import StudentInvitation
from app.university_ai.models.university import (
    University,
    Faculty,
    Department,
    Course,
    AcademicSession,
    AcademicSemester,
)
from app.university_ai.models.academic import (
    CourseOffering,
    LecturerCourse,
    StudentCourse,
)

from app.university_ai.models.course_document import CourseDocument

from app.university_ai.services.course_document_embeddings import build_course_document_chunks

from app.university_ai.services.course_documents import (
    save_course_document_file,
    extract_course_document_text,
)

from app.university_ai.services.lecturer_auth import require_lecturer

from app.university_ai.services.lecturer_assessment import (
    create_assessment,
    update_assessment,
    deactivate_assessment,
    list_assessments,
    save_student_score,
)

from app.university_ai.services.attendance import (
    mark_attendance,
    bulk_mark_attendance,
    update_attendance,
    get_student_attendance_history,
    get_course_attendance_summary,
    get_low_attendance_students,
    generate_lecturer_attendance_report,
)

from app.university_ai.services.lecturer_ai import (
    get_lecturer_profile,
    get_lecturer_courses,
    get_course_students,
    get_course_assessments_for_lecturer,
    get_course_score_summary,
    get_lecturer_dashboard,
)

from app.university_ai.services.student_importer import (
    preview_student_import,
    import_students,
)


router = APIRouter(
    prefix="/university/lecturer",
    tags=["University Lecturer"],
)

@router.get("/courses/{course_offering_id}/documents")
def get_course_documents(
    course_offering_id: int,
    db: Session = Depends(get_db),
    lecturer: Lecturer = Depends(require_lecturer),
):

    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    documents = (
        db.query(CourseDocument)
        .filter(
            CourseDocument.university_id == lecturer.university_id,
            CourseDocument.course_offering_id == course_offering_id,
        )
        .order_by(CourseDocument.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "documents": [
            {
                "id": document.id,
                "title": document.title,
                "original_filename": document.original_filename,
                "file_type": document.file_type,
                "status": document.status,
                "text_length": len(document.extracted_text or ""),
                "lecturer_id": document.lecturer_id,
                "created_at": document.created_at,
            }
            for document in documents
        ],
    }

@router.post("/courses/{course_offering_id}/documents")
async def upload_course_document(
    course_offering_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
    lecturer: Lecturer = Depends(require_lecturer),
):

    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded document is empty.",
        )

    filename = file.filename or "course_document"

    try:
        storage_path = save_course_document_file(
            file_bytes=file_bytes,
            filename=filename,
            university_id=lecturer.university_id,
            course_offering_id=course_offering_id,
        )

        extracted_text = extract_course_document_text(storage_path)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to process course document: {exc}",
        )

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No readable text could be extracted from this document.",
        )

    document_title = (
        title.strip()
        if title and title.strip()
        else Path(filename).stem
    )

    document = CourseDocument(
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
        lecturer_id=lecturer.id,
        title=document_title,
        original_filename=filename,
        file_path=str(storage_path),
        file_type=Path(filename).suffix.lower(),
        extracted_text=extracted_text,
        status="processed",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        chunk_count = build_course_document_chunks(
            db=db,
            document=document,
        )
    except Exception as exc:
        document.status = "processed"
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Document uploaded, but knowledge-base indexing failed: {exc}",
        )

    return {
        "success": True,
        "message": "Course document uploaded and processed successfully.",
        "document": {
            "id": document.id,
            "title": document.title,
            "original_filename": document.original_filename,
            "file_type": document.file_type,
            "status": document.status,
            "course_offering_id": document.course_offering_id,
            "lecturer_id": document.lecturer_id,
            "text_length": len(document.extracted_text or ""),
        },
    }



# ============================================================
# COURSE ACCESS
# ============================================================

def verify_course_access(
    db: Session,
    lecturer_id: int,
    university_id: int,
    course_offering_id: int,
):
    courses = get_lecturer_courses(
        db=db,
        university_id=university_id,
        lecturer_id=lecturer_id,
    )

    for course in courses:
        if course["course_offering_id"] == course_offering_id:
            return course

    raise HTTPException(
        status_code=403,
        detail="You are not assigned to this course.",
    )


# ============================================================
# LECTURER ONBOARDING
# ============================================================

@router.post("/onboard")
def onboard_lecturer(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(Lecturer)
        .filter(Lecturer.user_id == current_user.id)
        .first()
    )

    if existing:
        return {
            "success": True,
            "message": "Lecturer profile already exists.",
            "lecturer_id": existing.id,
            "university_id": existing.university_id,
        }

    first_name = str(payload.get("first_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()

    if not first_name or not last_name:
        raise HTTPException(
            status_code=400,
            detail="First name and last name are required.",
        )

    workspace = University(
        name=f"Private Lecturer Workspace - {current_user.id}",
        code=f"PRIVATE_LECTURER_{current_user.id}",
        country="PRIVATE",
        status="active",
    )

    db.add(workspace)
    db.flush()

    lecturer = Lecturer(
        user_id=current_user.id,
        university_id=workspace.id,
        staff_id=f"IND-{current_user.id}",
        first_name=first_name,
        middle_name=payload.get("middle_name"),
        last_name=last_name,
        title=payload.get("title"),
        academic_rank=payload.get("academic_rank"),
        specialization=payload.get("specialization"),
        phone=payload.get("phone"),
        is_department_head=False,
        status="active",
    )

    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)

    return {
        "success": True,
        "message": "Independent lecturer account created.",
        "mode": "independent",
        "lecturer_id": lecturer.id,
        "university_id": lecturer.university_id,
        "staff_id": lecturer.staff_id,
    }


# ============================================================
# LECTURER PROFILE
# ============================================================

@router.get("/me")
def lecturer_me(
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    return get_lecturer_profile(
        db=db,
        university_id=lecturer.university_id,
        lecturer_id=lecturer.id,
    )


# ============================================================
# LECTURER DASHBOARD
# ============================================================

@router.get("/dashboard")
def lecturer_dashboard(
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    return get_lecturer_dashboard(
        db=db,
        university_id=lecturer.university_id,
        lecturer_id=lecturer.id,
    )


# ============================================================
# INDEPENDENT COURSE CREATION
# ============================================================

@router.post("/courses")
def create_independent_course(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer: Lecturer = Depends(require_lecturer),
):
    university = (
        db.query(University)
        .filter(University.id == lecturer.university_id)
        .first()
    )

    if not university or not str(university.code or "").startswith(
        "PRIVATE_LECTURER_"
    ):
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only for independent lecturers.",
        )

    code = str(payload.get("code", "")).strip()
    title = str(payload.get("title", "")).strip()

    if not code or not title:
        raise HTTPException(
            status_code=400,
            detail="Course code and title are required.",
        )

    faculty = (
        db.query(Faculty)
        .filter(Faculty.university_id == university.id)
        .first()
    )

    if not faculty:
        faculty = Faculty(
            university_id=university.id,
            name="Independent Faculty",
            code=f"IF-{lecturer.id}",
            status="active",
        )

        db.add(faculty)
        db.flush()

    department = (
        db.query(Department)
        .filter(Department.university_id == university.id)
        .first()
    )

    if not department:
        department = Department(
            faculty_id=faculty.id,
            university_id=university.id,
            name="Independent Department",
            code=f"ID-{lecturer.id}",
            status="active",
        )

        db.add(department)
        db.flush()

    session = (
        db.query(AcademicSession)
        .filter(AcademicSession.university_id == university.id)
        .first()
    )

    if not session:
        session = AcademicSession(
            university_id=university.id,
            name="2026/2027",
            start_year=2026,
            end_year=2027,
            is_current=True,
            status="active",
        )

        db.add(session)
        db.flush()

    semester = (
        db.query(AcademicSemester)
        .filter(
            AcademicSemester.university_id == university.id,
            AcademicSemester.academic_session_id == session.id,
        )
        .first()
    )

    if not semester:
        semester = AcademicSemester(
            academic_session_id=session.id,
            university_id=university.id,
            name="First Semester",
            number=1,
            is_current=True,
            status="active",
        )

        db.add(semester)
        db.flush()

    course = Course(
        university_id=university.id,
        department_id=department.id,
        code=code,
        title=title,
        description=payload.get("description"),
        credit_units=payload.get("credit_units"),
        level=payload.get("level"),
        semester=payload.get("semester"),
        status="active",
    )

    db.add(course)
    db.flush()

    offering = CourseOffering(
        university_id=university.id,
        course_id=course.id,
        class_id=None,
        academic_session_id=session.id,
        semester_id=semester.id,
        level=payload.get("level"),
        section=payload.get("section"),
        status="active",
    )

    db.add(offering)
    db.flush()

    assignment = LecturerCourse(
        university_id=university.id,
        lecturer_id=lecturer.id,
        course_offering_id=offering.id,
        role="lecturer",
        can_manage_students=True,
        can_manage_assessments=True,
        can_manage_results=True,
        status="active",
    )

    db.add(assignment)
    db.commit()
    db.refresh(course)

    return {
        "success": True,
        "mode": "independent",
        "course_id": course.id,
        "course_offering_id": offering.id,
        "code": course.code,
        "title": course.title,
        "lecturer_id": lecturer.id,
    }


# ============================================================
# LECTURER COURSES
# ============================================================

@router.get("/courses")
def lecturer_courses(
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    return get_lecturer_courses(
        db=db,
        university_id=lecturer.university_id,
        lecturer_id=lecturer.id,
    )


# ============================================================
# COURSE STUDENTS
# ============================================================

@router.get("/courses/{course_offering_id}/students")
def lecturer_course_students(
    course_offering_id: int,
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    return get_course_students(
        db=db,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )


# ============================================================
# MANUAL SINGLE STUDENT ADD
# ============================================================

@router.post("/courses/{course_offering_id}/students")
def add_lecturer_student(
    course_offering_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_students", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage students for this course.",
        )

    university = (
        db.query(University)
        .filter(University.id == lecturer.university_id)
        .first()
    )

    if not university or not str(university.code or "").startswith(
        "PRIVATE_LECTURER_"
    ):
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only for independent lecturers.",
        )

    matric_number = str(payload.get("matric_number", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    first_name = str(payload.get("first_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()

    if not matric_number or not email or not first_name or not last_name:
        raise HTTPException(
            status_code=400,
            detail="Email, matric number, first name and last name are required.",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    existing_student = (
        db.query(Student)
        .filter(
            Student.university_id == lecturer.university_id,
            Student.matric_number == matric_number,
        )
        .first()
    )

    if existing_student:
        if existing_student.user_id is not None:
            if existing_user and existing_student.user_id == existing_user.id:
                raise HTTPException(
                    status_code=409,
                    detail="This student is already linked to this Aloko account.",
                )

            raise HTTPException(
                status_code=409,
                detail="A student with this matric number is already linked to another Aloko account.",
            )

        student = existing_student

        if existing_user:
            student.user_id = existing_user.id

    else:
        student = Student(
            user_id=existing_user.id if existing_user else None,
            university_id=lecturer.university_id,
            faculty_id=None,
            department_id=None,
            programme_id=None,
            matric_number=matric_number,
            first_name=first_name,
            middle_name=payload.get("middle_name"),
            last_name=last_name,
            level=payload.get("level"),
            entry_year=payload.get("entry_year"),
            graduation_year=payload.get("graduation_year"),
            phone=payload.get("phone"),
            status="active",
        )

        db.add(student)
        db.flush()

    enrollment = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.university_id == lecturer.university_id,
            StudentCourse.student_id == student.id,
            StudentCourse.course_offering_id == course_offering_id,
        )
        .first()
    )

    if not enrollment:
        enrollment = StudentCourse(
            university_id=lecturer.university_id,
            student_id=student.id,
            course_offering_id=course_offering_id,
            enrollment_status="enrolled",
        )
        db.add(enrollment)

    invitation = None

    if existing_user:
        result_mode = "linked_existing_account"
        message = "Student added and linked to the existing Aloko account."

    else:
        import secrets
        from datetime import datetime, timedelta, timezone

        token = secrets.token_urlsafe(32)

        invitation = StudentInvitation(
            email=email,
            university_id=lecturer.university_id,
            course_offering_id=course_offering_id,
            student_id=student.id,
            invited_by_lecturer_id=lecturer.id,
            token=token,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )

        db.add(invitation)

        result_mode = "invitation_created"
        message = "Student added. An invitation is pending for this email address."

    db.commit()
    db.refresh(student)

    if invitation:
        print("\n==============================================")
        print("ALOKO STUDENT INVITATION")
        print(f"Email: {email}")
        print(f"Course Offering ID: {course_offering_id}")
        print(f"Invitation Token: {invitation.token}")
        print("==============================================\n")

    return {
        "success": True,
        "mode": "independent",
        "result_mode": result_mode,
        "message": message,
        "student_id": student.id,
        "course_offering_id": course_offering_id,
        "email": email,
        "matric_number": student.matric_number,
        "first_name": student.first_name,
        "middle_name": student.middle_name,
        "last_name": student.last_name,
        "level": student.level,
        "enrollment_status": enrollment.enrollment_status,
        "invitation_created": invitation is not None,
    }



# ============================================================
# BULK STUDENT IMPORT Ã¢â‚¬â€ PREVIEW
# ============================================================

@router.post("/courses/{course_offering_id}/students/import/preview")
async def lecturer_preview_student_import(
    course_offering_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    """
    Preview a student import without modifying the database.

    The existing student_importer service performs:
    - file reading
    - column detection
    - student extraction
    - validation
    - duplicate detection
    """

    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_students", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage students for this course.",
        )

    filename = file.filename or "student_import"

    try:
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        preview = preview_student_import(
            db=db,
            university_id=lecturer.university_id,
            file_bytes=file_bytes,
            filename=filename,
        )

        return {
            "success": preview["validation"]["valid"],
            "mode": "preview",
            "course_offering_id": course_offering_id,
            **preview,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Student import preview failed: {exc}",
        )


# ============================================================
# BULK STUDENT IMPORT Ã¢â‚¬â€ COMMIT
# ============================================================

@router.post("/courses/{course_offering_id}/students/import")
async def lecturer_import_students(
    course_offering_id: int,
    file: UploadFile = File(...),
    update_existing: bool = Form(True),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    """
    Import many students into the lecturer workspace.

    Workflow:

        Upload
          Ã¢â€ â€œ
        Validate
          Ã¢â€ â€œ
        Import/update students
          Ã¢â€ â€œ
        Automatically enroll them in this course

    This is for independent lecturers and does not require
    linking a university portal.
    """

    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_students", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage students for this course.",
        )

    university = (
        db.query(University)
        .filter(University.id == lecturer.university_id)
        .first()
    )

    filename = file.filename or "student_import"

    try:
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        # ----------------------------------------------------
        # STEP 1 Ã¢â‚¬â€ PREVIEW / VALIDATE
        # ----------------------------------------------------

        preview = preview_student_import(
            db=db,
            university_id=lecturer.university_id,
            file_bytes=file_bytes,
            filename=filename,
        )

        if not preview["validation"]["valid"]:
            return {
                "success": False,
                "mode": "commit",
                "message": (
                    "Import blocked. Fix the validation errors "
                    "before importing."
                ),
                "course_offering_id": course_offering_id,
                **preview,
            }

        # ----------------------------------------------------
        # STEP 2 Ã¢â‚¬â€ IMPORT STUDENTS
        # ----------------------------------------------------

        result = import_students(
            db=db,
            university_id=lecturer.university_id,
            students=preview["students"],
            update_existing=update_existing,
        )

        if not result["success"]:
            return {
                **result,
                "mode": "commit",
                "course_offering_id": course_offering_id,
                "validation": preview["validation"],
                "detected_columns": preview["detected_columns"],
            }

        # ----------------------------------------------------
        # STEP 3 Ã¢â‚¬â€ FIND IMPORTED / EXISTING STUDENTS
        # ----------------------------------------------------

        matric_numbers = [
            student["matric_number"]
            for student in preview["students"]
            if student.get("matric_number")
        ]

        students = []

        if matric_numbers:
            students = (
                db.query(Student)
                .filter(
                    Student.university_id == lecturer.university_id,
                    Student.matric_number.in_(matric_numbers),
                )
                .all()
            )

        # ----------------------------------------------------
        # STEP 4 Ã¢â‚¬â€ ENROLL STUDENTS INTO THIS COURSE
        # ----------------------------------------------------

        enrolled = 0
        already_enrolled = 0

        for student in students:

            existing_enrollment = (
                db.query(StudentCourse)
                .filter(
                    StudentCourse.university_id == lecturer.university_id,
                    StudentCourse.student_id == student.id,
                    StudentCourse.course_offering_id == course_offering_id,
                )
                .first()
            )

            if existing_enrollment:
                already_enrolled += 1
                continue

            enrollment = StudentCourse(
                university_id=lecturer.university_id,
                student_id=student.id,
                course_offering_id=course_offering_id,
                enrollment_status="enrolled",
            )

            db.add(enrollment)
            enrolled += 1

        db.commit()

        return {
            **result,
            "mode": "commit",
            "course_offering_id": course_offering_id,
            "validation": preview["validation"],
            "detected_columns": preview["detected_columns"],
            "enrollment": {
                "enrolled": enrolled,
                "already_enrolled": already_enrolled,
                "total_students_found": len(students),
            },
        }

    except HTTPException:
        raise

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Student import failed: {exc}",
        )


# ============================================================
# COURSE ASSESSMENTS
# ============================================================

@router.get("/courses/{course_offering_id}/assessments")
def lecturer_course_assessments(
    course_offering_id: int,
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    return get_course_assessments_for_lecturer(
        db=db,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )


# ============================================================
# CREATE ASSESSMENT
# ============================================================

@router.post("/courses/{course_offering_id}/assessments")
def lecturer_create_assessment(
    course_offering_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_assessments", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage assessments for this course.",
        )

    try:
        assessment = create_assessment(
            db=db,
            university_id=lecturer.university_id,
            course_offering_id=course_offering_id,
            title=payload.get("title"),
            assessment_type=payload.get("assessment_type"),
            max_score=payload.get("max_score"),
            created_by=lecturer.id,
            weight=payload.get("weight"),
            description=payload.get("description"),
            assessment_date=payload.get("assessment_date"),
        )

        return {
            "id": assessment.id,
            "title": assessment.title,
            "assessment_type": assessment.assessment_type,
            "description": assessment.description,
            "max_score": assessment.max_score,
            "weight": assessment.weight,
            "assessment_date": assessment.assessment_date,
            "is_published": assessment.is_published,
            "status": assessment.status,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# UPDATE ASSESSMENT
# ============================================================

@router.put("/courses/{course_offering_id}/assessments/{assessment_id}")
def lecturer_update_assessment(
    course_offering_id: int,
    assessment_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_assessments", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage assessments for this course.",
        )

    from app.university_ai.models import Assessment

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.university_id == lecturer.university_id,
            Assessment.course_offering_id == course_offering_id,
        )
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found for this course.",
        )

    allowed_fields = {
        "title",
        "assessment_type",
        "max_score",
        "weight",
        "description",
        "assessment_date",
    }

    updates = {
        key: value
        for key, value in payload.items()
        if key in allowed_fields
    }

    try:
        updated = update_assessment(
            db=db,
            university_id=lecturer.university_id,
            assessment_id=assessment_id,
            **updates,
        )

        return {
            "id": updated.id,
            "title": updated.title,
            "assessment_type": updated.assessment_type,
            "description": updated.description,
            "max_score": updated.max_score,
            "weight": updated.weight,
            "assessment_date": updated.assessment_date,
            "is_published": updated.is_published,
            "status": updated.status,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# DEACTIVATE ASSESSMENT
# ============================================================

@router.delete("/courses/{course_offering_id}/assessments/{assessment_id}")
def lecturer_deactivate_assessment(
    course_offering_id: int,
    assessment_id: int,
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_assessments", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage assessments for this course.",
        )

    from app.university_ai.models import Assessment

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.university_id == lecturer.university_id,
            Assessment.course_offering_id == course_offering_id,
        )
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found for this course.",
        )

    try:
        deleted = deactivate_assessment(
            db=db,
            university_id=lecturer.university_id,
            assessment_id=assessment_id,
        )

        return {
            "success": True,
            "message": "Assessment deactivated successfully.",
            "assessment": {
                "id": deleted.id,
                "title": deleted.title,
                "status": deleted.status,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# SAVE STUDENT SCORE
# ============================================================

@router.post("/courses/{course_offering_id}/scores")
def lecturer_save_student_score(
    course_offering_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_results", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage results for this course.",
        )

    try:
        student_id = int(payload.get("student_id"))
        assessment_id = int(payload.get("assessment_id"))

        score_value = payload.get("score")

        score = (
            None
            if score_value in (None, "")
            else float(score_value)
        )

        is_absent = bool(payload.get("is_absent", False))

        result = save_student_score(
            db=db,
            university_id=lecturer.university_id,
            student_id=student_id,
            assessment_id=assessment_id,
            score=score,
            marked_by=lecturer.id,
            is_absent=is_absent,
            lecturer_comment=payload.get("lecturer_comment"),
        )

        return {
            "success": True,
            "id": result.id,
            "student_id": result.student_id,
            "assessment_id": result.assessment_id,
            "course_offering_id": result.course_offering_id,
            "score": result.score,
            "percentage": result.percentage,
            "status": result.status,
            "is_absent": result.is_absent,
            "lecturer_comment": result.lecturer_comment,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# MARK ATTENDANCE
# ============================================================

@router.post("/courses/{course_offering_id}/attendance")
def lecturer_mark_attendance(
    course_offering_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_students", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage attendance for this course.",
        )

    try:
        from datetime import date

        raw_date = payload.get("attendance_date")

        attendance_date = (
            date.fromisoformat(raw_date)
            if isinstance(raw_date, str)
            else raw_date
        )

        student_id = int(payload.get("student_id"))

        record = mark_attendance(
            db=db,
            university_id=lecturer.university_id,
            course_offering_id=course_offering_id,
            student_id=student_id,
            attendance_date=attendance_date,
            status=payload.get("status", "present"),
            marked_by=lecturer.id,
            note=payload.get("note"),
        )

        return {
            "success": True,
            "id": record.id,
            "student_id": record.student_id,
            "course_offering_id": record.course_offering_id,
            "attendance_date": record.attendance_date,
            "status": record.status,
            "note": record.note,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# BULK ATTENDANCE
# ============================================================

@router.post("/courses/{course_offering_id}/attendance/bulk")
def lecturer_bulk_attendance(
    course_offering_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_students", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage attendance for this course.",
        )

    try:
        from datetime import date

        raw_date = payload.get("attendance_date")

        attendance_date = (
            date.fromisoformat(raw_date)
            if isinstance(raw_date, str)
            else raw_date
        )

        records = payload.get("records", [])

        if not isinstance(records, list) or not records:
            raise ValueError("Attendance records are required.")

        results = bulk_mark_attendance(
            db=db,
            university_id=lecturer.university_id,
            course_offering_id=course_offering_id,
            attendance_date=attendance_date,
            records=records,
            marked_by=lecturer.id,
        )

        return {
            "success": True,
            "count": len(results),
            "records": [
                {
                    "id": record.id,
                    "student_id": record.student_id,
                    "status": record.status,
                    "attendance_date": record.attendance_date,
                    "note": record.note,
                }
                for record in results
            ],
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# UPDATE ATTENDANCE
# ============================================================

@router.put("/courses/{course_offering_id}/attendance/{attendance_id}")
def lecturer_update_attendance(
    course_offering_id: int,
    attendance_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    course = verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    if not course.get("can_manage_students", False):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage attendance for this course.",
        )

    from app.university_ai.models.attendance import AttendanceRecord

    record = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.id == attendance_id,
            AttendanceRecord.university_id == lecturer.university_id,
            AttendanceRecord.course_offering_id == course_offering_id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found for this course.",
        )

    try:
        updated = update_attendance(
            db=db,
            attendance_id=attendance_id,
            status=payload.get("status"),
            note=payload.get("note"),
        )

        return {
            "success": True,
            "id": updated.id,
            "student_id": updated.student_id,
            "course_offering_id": updated.course_offering_id,
            "attendance_date": updated.attendance_date,
            "status": updated.status,
            "note": updated.note,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# COURSE ATTENDANCE SUMMARY
# ============================================================

@router.get("/courses/{course_offering_id}/attendance")
def lecturer_course_attendance(
    course_offering_id: int,
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    return get_course_attendance_summary(
        db=db,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )


# ============================================================
# ATTENDANCE REPORT
# ============================================================

@router.get("/courses/{course_offering_id}/attendance/report")
def lecturer_attendance_report(
    course_offering_id: int,
    threshold: float = 75.0,
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    return generate_lecturer_attendance_report(
        db=db,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
        low_attendance_threshold=threshold,
    )


# ============================================================
# LOW ATTENDANCE
# ============================================================

@router.get("/courses/{course_offering_id}/attendance/low")
def lecturer_low_attendance(
    course_offering_id: int,
    threshold: float = 75.0,
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    return get_low_attendance_students(
        db=db,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
        threshold=threshold,
    )



# ============================================================
# COURSE RESULTS EXPORT
# ============================================================

def _result_grade(percentage):
    if percentage is None:
        return ""
    percentage = float(percentage)
    if percentage >= 70:
        return "A"
    if percentage >= 60:
        return "B"
    if percentage >= 50:
        return "C"
    if percentage >= 45:
        return "D"
    if percentage >= 40:
        return "E"
    return "F"


@router.get("/courses/{course_offering_id}/results/export")
def export_course_results(
    course_offering_id: int,
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    db: Session = Depends(get_db),
    lecturer: Lecturer = Depends(require_lecturer),
):
    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    result_data = get_course_score_summary(
        db=db,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    assessments = (
        result_data["students"][0].get("assessments", [])
        if result_data.get("students")
        else []
    )

    headers = (
        ["S/N", "Student Name", "Matric Number"]
        + [
            f"{a['title']} ({a['max_score']})"
            for a in assessments
        ]
        + [
            "Total Score",
            "Total Maximum",
            "Percentage",
            "Grade",
        ]
    )

    rows = []

    for index, student in enumerate(
        result_data.get("students", []), 1
    ):
        scores = student.get("assessments", [])

        total_max = sum(
            float(a.get("max_score") or 0)
            for a in scores
        )

        total_score = sum(
            float(a.get("score") or 0)
            for a in scores
            if not a.get("is_absent")
        )

        percentage = (
            total_score / total_max * 100
            if total_max
            else 0
        )

        name = " ".join(
            str(value).strip()
            for value in [
                student.get("first_name"),
                student.get("middle_name"),
                student.get("last_name"),
            ]
            if value
        ).strip()

        assessment_values = [
            (
                "Absent"
                if a.get("is_absent")
                else (
                    a.get("score")
                    if a.get("score") is not None
                    else "Missing"
                )
            )
            for a in scores
        ]

        has_mark = any(
            a.get("score") is not None
            or a.get("is_absent")
            for a in scores
        )

        rows.append(
            [
                index,
                name,
                (
                    student.get("matric_number")
                    or student.get("registration_number")
                    or student.get("student_id")
                ),
            ]
            + assessment_values
            + [
                round(total_score, 2),
                round(total_max, 2),
                round(percentage, 2),
                _result_grade(percentage)
                if has_mark
                else "",
            ]
        )

    # CSV
    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerows([headers] + rows)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    f'attachment; filename="course-results-{course_offering_id}.csv"'
            },
        )

    # Excel
    if format == "xlsx":
        from openpyxl import Workbook

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Results"

        worksheet.append(headers)

        for row in rows:
            worksheet.append(row)

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for column in worksheet.columns:
            letter = column[0].column_letter
            width = max(
                len(str(cell.value or ""))
                for cell in column
            ) + 2

            worksheet.column_dimensions[letter].width = min(
                max(width, 12),
                35,
            )

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition":
                    f'attachment; filename="course-results-{course_offering_id}.xlsx"'
            },
        )

    # PDF
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
    )

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

    story = [
        Paragraph(
            "Course Student Results",
            styles["Title"],
        )
    ]

    table = Table(
        [headers] + rows,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
            ]
        )
    )

    story.append(table)

    document.build(story)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="course-results-{course_offering_id}.pdf"'
        },
    )

# ============================================================
# COURSE SCORES
# ============================================================

@router.get("/courses/{course_offering_id}/scores")
def lecturer_course_scores(
    course_offering_id: int,
    db: Session = Depends(get_db),
    lecturer=Depends(require_lecturer),
):
    verify_course_access(
        db=db,
        lecturer_id=lecturer.id,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )

    return get_course_score_summary(
        db=db,
        university_id=lecturer.university_id,
        course_offering_id=course_offering_id,
    )


