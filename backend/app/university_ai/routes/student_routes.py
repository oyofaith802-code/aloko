from pathlib import Path
import mimetypes

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.university_ai.services.student_auth import require_student
from app.university_ai.services.student_dashboard import get_student_dashboard
from app.university_ai.services.course_ai import ask_course_ai
from app.university_ai.models.course_document import CourseDocument
from app.university_ai.models.academic import StudentCourse


router = APIRouter(
    prefix="/university/student",
    tags=["University Student"],
)


class CourseAIQuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )


def verify_student_course_enrollment(
    db: Session,
    student,
    course_offering_id: int,
):
    enrollment = (
        db.query(StudentCourse)
        .filter(
            StudentCourse.university_id == student.university_id,
            StudentCourse.student_id == student.id,
            StudentCourse.course_offering_id == course_offering_id,
            StudentCourse.enrollment_status == "enrolled",
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this course.",
        )

    return enrollment


@router.get("/me")
def student_me(
    student=Depends(require_student),
):
    return {
        "id": student.id,
        "matric_number": student.matric_number,
        "first_name": student.first_name,
        "middle_name": student.middle_name,
        "last_name": student.last_name,
        "level": student.level,
        "university_id": student.university_id,
    }


@router.get("/dashboard")
def student_dashboard(
    student=Depends(require_student),
    db: Session = Depends(get_db),
):
    return get_student_dashboard(
        db=db,
        student=student,
    )


@router.get("/courses/{course_offering_id}/documents")
def get_student_course_documents(
    course_offering_id: int,
    student=Depends(require_student),
    db: Session = Depends(get_db),
):
    verify_student_course_enrollment(
        db=db,
        student=student,
        course_offering_id=course_offering_id,
    )

    documents = (
        db.query(CourseDocument)
        .filter(
            CourseDocument.university_id == student.university_id,
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
                "created_at": document.created_at,
            }
            for document in documents
        ],
    }


@router.get("/courses/{course_offering_id}/documents/{document_id}/download")
def download_student_course_document(
    course_offering_id: int,
    document_id: int,
    student=Depends(require_student),
    db: Session = Depends(get_db),
):
    verify_student_course_enrollment(
        db=db,
        student=student,
        course_offering_id=course_offering_id,
    )

    document = (
        db.query(CourseDocument)
        .filter(
            CourseDocument.id == document_id,
            CourseDocument.university_id == student.university_id,
            CourseDocument.course_offering_id == course_offering_id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Course material not found.",
        )

    if not document.file_path:
        raise HTTPException(
            status_code=404,
            detail="The original course material file is not available.",
        )

    file_path = Path(document.file_path)

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="The course material file could not be found on the server.",
        )

    media_type = (
        mimetypes.guess_type(document.original_filename)[0]
        or "application/octet-stream"
    )

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=document.original_filename,
    )


@router.post("/courses/{course_offering_id}/ask")
def ask_course_question(
    course_offering_id: int,
    payload: CourseAIQuestionRequest,
    student=Depends(require_student),
    db: Session = Depends(get_db),
):
    try:
        return ask_course_ai(
            db=db,
            student_id=student.id,
            university_id=student.university_id,
            course_offering_id=course_offering_id,
            question=payload.question,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Course AI failed: {exc}",
        )

