import json

from typing import List, Annotated

from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.university_ai.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentSubmission,
    AIMarkingJob,
    AIMarkingResult,
)

from app.university_ai.models.people import Student, Lecturer
from app.university_ai.models.university import Department

from app.university_ai.models.attendance import AttendanceRecord
from app.university_ai.models.academic import StudentCourse

from app.university_ai.services.ai_marking import (
    save_marking_file,
    extract_matric_number,
    find_student_by_matric,
    verify_student_enrollment,
    create_submission,
    extract_question_paper,
    extract_submission_text,
    parse_questions,
    create_question,
    create_marking_job,
    create_marking_result,
    mark_answer_with_ai,
    extract_student_answers,
)

from app.university_ai.services.lecturer_assessment import (
    save_student_score,
)

from app.university_ai.services.lecturer_auth import require_lecturer

router = APIRouter(
    prefix="/university/ai-marking",
    tags=["University AI Marking"],
)


# ============================================================
# AI MARKING AUTHORIZATION
# ============================================================

def verify_ai_marking_access(
    db: Session,
    lecturer: Lecturer,
    assessment_id: int,
    required_permission: str,
):
    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id,
            Assessment.university_id == lecturer.university_id,
            Assessment.status == "active",
        )
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found.",
        )

    from app.university_ai.services.lecturer_ai import get_lecturer_courses

    courses = get_lecturer_courses(
        db=db,
        university_id=lecturer.university_id,
        lecturer_id=lecturer.id,
    )

    course = next(
        (
            item
            for item in courses
            if item["course_offering_id"] == assessment.course_offering_id
        ),
        None,
    )

    if not course:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this course.",
        )

    if not course.get(required_permission, False):
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to {required_permission.replace('_', ' ')} for this course.",
        )

    return assessment, course

# ============================================================
# UPLOAD QUESTION PAPER
# ============================================================

@router.post(
    "/assessments/{assessment_id}/upload-question-paper"
)
async def upload_question_paper(
    assessment_id: int,
    file: UploadFile = File(...),
    lecturer: Lecturer = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    assessment, course = verify_ai_marking_access(
        db=db,
        lecturer=lecturer,
        assessment_id=assessment_id,
        required_permission="can_manage_assessments",
    )

    filename = file.filename or ""

    extension = (
        "." + filename.rsplit(".", 1)[-1].lower()
        if "." in filename
        else ""
    )

    allowed_extensions = {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".heic",
        ".heif",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported question paper format. "
                "Supported formats: PDF, DOC, DOCX, TXT, JPG, "
                "JPEG, PNG, WEBP, HEIC and HEIF."
            ),
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded question paper is empty.",
        )

    try:
        storage_path = save_marking_file(
            file_bytes,
            filename,
            lecturer.university_id,
            assessment_id,
        )

        extracted = extract_question_paper(
            storage_path
        )

        questions = parse_questions(
            extracted.get("text", "")
        )

        if not questions:
            raise HTTPException(
                status_code=400,
                detail="No questions could be detected.",
            )

        missing_marks = [
            q["question_number"]
            for q in questions
            if q["max_score"] is None
        ]

        if missing_marks:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Some questions are missing marks.",
                    "questions_missing_marks": missing_marks,
                },
            )

        existing = (
            db.query(AssessmentQuestion)
            .filter(
                AssessmentQuestion.university_id == lecturer.university_id,
                AssessmentQuestion.assessment_id == assessment_id,
            )
            .all()
        )

        existing_numbers = {
            q.question_number
            for q in existing
        }

        created = []

        for item in questions:
            if item["question_number"] in existing_numbers:
                continue

            question = create_question(
                db=db,
                university_id=lecturer.university_id,
                assessment_id=assessment_id,
                question_number=item["question_number"],
                question_text=item["question_text"],
                max_score=float(item["max_score"]),
                created_by=assessment.created_by,
            )

            created.append(
                {
                    "id": question.id,
                    "question_number": question.question_number,
                    "question_text": question.question_text,
                    "max_score": question.max_score,
                }
            )

        return {
            "assessment_id": assessment_id,
            "file_name": filename,
            "detected_questions": len(questions),
            "created_questions": len(created),
            "questions": created,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# UPLOAD STUDENT ANSWER PAPERS
# ============================================================

@router.post(
    "/assessments/{assessment_id}/upload-answers"
)
async def upload_student_answer_papers(
    assessment_id: int,
    files: Annotated[List[UploadFile], File(...)],
    lecturer: Lecturer = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    """
    Upload student answer papers.

    Student identity is OPTIONAL at upload time.

    Supported cases:

    1. Filename contains a valid matric number
       -> student is identified automatically.

    2. Filename does not contain a matric number
       -> paper is uploaded with:
          student_id = None
          status = "pending_student_match"

    3. Filename contains a matric number but the student
       cannot be found
       -> paper is uploaded with:
          student_id = None
          status = "pending_student_match"

    The system never guesses student identity.
    """

    assessment, course = verify_ai_marking_access(
        db=db,
        lecturer=lecturer,
        assessment_id=assessment_id,
        required_permission="can_manage_assessments",
    )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No answer papers were uploaded.",
        )

    results = []

    for file in files:
        filename = file.filename or "unknown_file"

        try:
            # ------------------------------------------------
            # READ FILE
            # ------------------------------------------------

            file_bytes = await file.read()

            if not file_bytes:
                results.append(
                    {
                        "file_name": filename,
                        "status": "rejected",
                        "reason": "Uploaded file is empty.",
                    }
                )
                continue

            # ------------------------------------------------
            # SAVE FILE
            # ------------------------------------------------

            storage_path = save_marking_file(
                file_bytes,
                filename,
                lecturer.university_id,
                assessment_id,
            )

            # ------------------------------------------------
            # EXTRACT TEXT
            # ------------------------------------------------

            extracted_text = extract_submission_text(
                storage_path
            )

            if not extracted_text or not extracted_text.strip():
                results.append(
                    {
                        "file_name": filename,
                        "status": "rejected",
                        "reason": (
                            "No readable answer text "
                            "could be extracted."
                        ),
                    }
                )
                continue

            # ------------------------------------------------
            # TRY TO IDENTIFY STUDENT
            # ------------------------------------------------

            student = None
            matric = None

            identity_status = "pending_student_match"

            identity_reason = (
                "Student identity was not provided. "
                "Lecturer matching is required."
            )

            # Matric number in filename is OPTIONAL.
            try:
                matric = extract_matric_number(
                    filename
                )
            except Exception:
                matric = None

            # ------------------------------------------------
            # AUTOMATIC STUDENT IDENTIFICATION
            # ------------------------------------------------

            if matric:
                student = find_student_by_matric(
                    db,
                    lecturer.university_id,
                    matric,
                )

                if student:
                    department_id = course.get("department_id")

                    department = (
                        db.query(Department)
                        .filter(Department.id == department_id)
                        .first()
                    )

                    independent_mode = (
                        department is not None
                        and department.name.strip().casefold()
                        == "independent department"
                    )

                    if independent_mode:
                        identity_status = "uploaded"
                        identity_reason = (
                            "Student identified from matric number "
                            "in an independent lecturer workspace."
                        )
                    else:
                        enrolled = verify_student_enrollment(
                            db,
                            student.id,
                            assessment.course_offering_id,
                        )

                        if enrolled:
                            identity_status = "uploaded"
                            identity_reason = (
                                "Student identified from matric number "
                                "in filename."
                            )
                        else:
                            student = None
                            identity_status = "pending_student_match"
                            identity_reason = (
                                "Student was found, but is not "
                                "enrolled in this course."
                            )
                else:
                    identity_status = "pending_student_match"
                    identity_reason = (
                        f"Matric number '{matric}' "
                        "was found in the filename, "
                        "but the student could not be found."
                    )

            submission = create_submission(
                db=db,
                university_id=lecturer.university_id,
                assessment_id=assessment_id,
                student_id=(
                    student.id
                    if student
                    else None
                ),
                file_name=filename,
                file_path=str(storage_path),
                extracted_text=extracted_text,
            )

            # ------------------------------------------------
            # UPDATE SUBMISSION STATUS
            # ------------------------------------------------

            submission.status = identity_status

            db.commit()
            db.refresh(submission)

            # ------------------------------------------------
            # BUILD RESPONSE
            # ------------------------------------------------

            result = {
                "file_name": filename,
                "submission_id": submission.id,
                "status": submission.status,
                "identity_reason": identity_reason,
            }

            if student:
                result.update(
                    {
                        "student_id": student.id,
                        "student_name": (
                            f"{student.first_name} "
                            f"{student.last_name}"
                        ),
                        "matric_number": (
                            student.matric_number
                        ),
                    }
                )

            else:
                result.update(
                    {
                        "student_id": None,
                        "student_name": None,
                        "matric_number": matric,
                    }
                )

            results.append(result)

        except Exception as exc:
            db.rollback()

            results.append(
                {
                    "file_name": filename,
                    "status": "error",
                    "reason": str(exc),
                }
            )

    uploaded_files = sum(
        1
        for item in results
        if item["status"] in {
            "uploaded",
            "pending_student_match",
        }
    )

    pending_student_match = sum(
        1
        for item in results
        if item["status"] == "pending_student_match"
    )

    return {
        "assessment_id": assessment_id,
        "total_files": len(files),
        "uploaded_files": uploaded_files,
        "pending_student_match": pending_student_match,
        "results": results,
    }


# ============================================================
# RUN AI MARKING
# ============================================================

@router.post(
    "/assessments/{assessment_id}/run-marking"
)
def run_ai_marking(
    assessment_id: int,
    submission_ids: list[int] = Body(..., embed=True),
    lecturer: Lecturer = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    assessment, course = verify_ai_marking_access(
        db=db,
        lecturer=lecturer,
        assessment_id=assessment_id,
        required_permission="can_manage_assessments",
    )

    # --------------------------------------------------------
    # ASSESSMENT DATE IS REQUIRED
    # --------------------------------------------------------

    if not assessment.assessment_date:
        raise HTTPException(
            status_code=400,
            detail=(
                "This assessment has no assessment date. "
                "Set the assessment date before running AI marking."
            ),
        )

    # --------------------------------------------------------
    # GET QUESTIONS
    # --------------------------------------------------------

    questions = (
        db.query(AssessmentQuestion)
        .filter(
            AssessmentQuestion.university_id
            == lecturer.university_id,
            AssessmentQuestion.assessment_id
            == assessment_id,
        )
        .order_by(
            AssessmentQuestion.id
        )
        .all()
    )

    # --------------------------------------------------------
    # GET SUBMISSIONS
    # --------------------------------------------------------

    # --------------------------------------------------------
    # ONLY PROCESS THE SUBMISSIONS FROM THE CURRENT UPLOAD BATCH
    # --------------------------------------------------------

    if not submission_ids:
        raise HTTPException(
            status_code=400,
            detail="No uploaded submission IDs were provided.",
        )

    # Remove duplicate IDs while preserving upload order.
    submission_ids = list(dict.fromkeys(submission_ids))

    submissions = (
        db.query(AssessmentSubmission)
        .filter(
            AssessmentSubmission.university_id
            == lecturer.university_id,
            AssessmentSubmission.assessment_id
            == assessment_id,
            AssessmentSubmission.id.in_(submission_ids),
        )
        .all()
    )

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="No assessment questions exist.",
        )

    if not submissions:
        raise HTTPException(
            status_code=400,
            detail="None of the uploaded submissions belong to this assessment.",
        )

    found_submission_ids = {submission.id for submission in submissions}

    missing_submission_ids = [
        submission_id
        for submission_id in submission_ids
        if submission_id not in found_submission_ids
    ]

    if missing_submission_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "Some uploaded submission IDs were not found for this assessment: "
                + ", ".join(map(str, missing_submission_ids))
            ),
        )

    # --------------------------------------------------------
    # CREATE MARKING JOB
    # --------------------------------------------------------

    job = create_marking_job(
        db=db,
        university_id=lecturer.university_id,
        assessment_id=assessment_id,
        created_by=assessment.created_by,
        submission_ids=submission_ids,
    )

    job.processed_submissions = 0
    job.status = "running"

    db.commit()
    db.refresh(job)

    total_results = 0
    processed_students = 0
    pending_identity = 0
    pending_integrity = 0

    department_id = course.get("department_id")

    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    independent_mode = (
        department is not None
        and department.name.strip().casefold()
        == "independent department"
    )

    try:
        # ----------------------------------------------------
        # PROCESS EACH SUBMISSION
        # ----------------------------------------------------

        for submission in submissions:

            # ------------------------------------------------
            # 1. STUDENT MUST BE IDENTIFIED
            # ------------------------------------------------

            if submission.student_id is None:
                pending_identity += 1
                continue

            student_id = submission.student_id

            # ------------------------------------------------
            # 2 + 3. VERIFY ENROLLMENT AND ATTENDANCE
            #
            # Connected university mode requires both checks.
            # Independent lecturer mode does not.

            if not independent_mode:

                enrolled = (
                    db.query(StudentCourse)
                    .filter(
                        StudentCourse.university_id
                        == lecturer.university_id,
                        StudentCourse.course_offering_id
                        == assessment.course_offering_id,
                        StudentCourse.student_id
                        == student_id,
                        StudentCourse.enrollment_status
                        == "enrolled",
                    )
                    .first()
                )

                if not enrolled:
                    pending_integrity += 1
                    continue

                attendance = (
                    db.query(AttendanceRecord)
                    .filter(
                        AttendanceRecord.university_id
                        == lecturer.university_id,
                        AttendanceRecord.course_offering_id
                        == assessment.course_offering_id,
                        AttendanceRecord.student_id
                        == student_id,
                        func.date(
                            AttendanceRecord.attendance_date
                        )
                        == assessment.assessment_date.date(),
                    )
                    .first()
                )

                if (
                    not attendance
                    or attendance.status
                    not in {
                        "present",
                        "late",
                    }
                ):
                    pending_integrity += 1
                    continue

            # 4. GET ANSWER TEXT
            # ------------------------------------------------

            answer_text = (
                submission.extracted_text
                or ""
            ).strip()

            if not answer_text:
                continue

            # ------------------------------------------------
            # 5. SPLIT PAPER INTO INDIVIDUAL ANSWERS
            # ------------------------------------------------

            student_answers = extract_student_answers(
                answer_text
            )

            # ------------------------------------------------
            # 6. MARK EACH QUESTION
            # ------------------------------------------------

            for question in questions:

                question_number = str(
                    question.question_number
                ).strip()

                student_answer = (
                    student_answers.get(
                        question_number,
                        "",
                    )
                    .strip()
                )

                result = mark_answer_with_ai(
                    question,
                    student_answer,
                )

                create_marking_result(
                    db=db,
                    university_id=lecturer.university_id,
                    job_id=job.id,
                    submission_id=submission.id,
                    question_id=question.id,
                    student_id=student_id,
                    extracted_answer=student_answer,
                    suggested_score=result["score"],
                    max_score=question.max_score,
                    confidence=result["confidence"],
                    grading_evidence=(
                        result["grading_evidence"]
                    ),
                    feedback=result["feedback"],
                )

                total_results += 1

            # ------------------------------------------------
            # MARK STUDENT AS PROCESSED
            # ------------------------------------------------

            processed_students += 1

            job.processed_submissions = (
                processed_students
            )

            db.commit()

        # ----------------------------------------------------
        # COMPLETE JOB
        # ----------------------------------------------------

        job.status = "completed"

        job.completed_at = datetime.now(
            timezone.utc
        )

        db.commit()

    except Exception as exc:
        db.rollback()

        failed_job = (
            db.query(AIMarkingJob)
            .filter(
                AIMarkingJob.id == job.id,
                AIMarkingJob.university_id
                == lecturer.university_id,
            )
            .first()
        )

        if failed_job:
            failed_job.status = "failed"
            failed_job.error_message = str(exc)

            db.commit()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "job_id": job.id,
        "assessment_id": assessment_id,
        "status": job.status,
        "total_submissions": job.total_submissions,

        "students_processed": (
            job.processed_submissions
        ),

        "submissions_pending_student_match": (
            pending_identity
        ),

        "submissions_pending_integrity_check": (
            pending_integrity
        ),

        "marking_results_created": (
            total_results
        ),

        "message": (
            "AI marking completed. "
            f"{pending_identity} submission(s) "
            "still require student identification. "
            f"{pending_integrity} submission(s) "
            "failed enrollment or attendance verification."
            if pending_identity or pending_integrity
            else "AI marking completed successfully."
        ),
    }


# ============================================================
# GET MARKING RESULTS
# ============================================================

@router.get(
    "/jobs/{job_id}/results"
)
def get_marking_results(
    job_id: int,
    lecturer: Lecturer = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    job = (
        db.query(AIMarkingJob)
        .filter(
            AIMarkingJob.id == job_id,
            AIMarkingJob.university_id == lecturer.university_id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="AI marking job not found.",
        )

    assessment, course = verify_ai_marking_access(
        db=db,
        lecturer=lecturer,
        assessment_id=job.assessment_id,
        required_permission="can_manage_results",
    )

    results = (
        db.query(AIMarkingResult)
        .filter(
            AIMarkingResult.job_id == job_id,
            AIMarkingResult.university_id == lecturer.university_id,
        )
        .order_by(
            AIMarkingResult.student_id,
            AIMarkingResult.question_id,
        )
        .all()
    )

    # --------------------------------------------------------
    # FIND SUBMISSIONS THAT STILL NEED STUDENT IDENTIFICATION
    # --------------------------------------------------------

    pending_submissions = []

    if job.submission_ids:
        try:
            tracked_submission_ids = json.loads(job.submission_ids)
        except (TypeError, ValueError):
            tracked_submission_ids = []

        if tracked_submission_ids:
            submissions = (
                db.query(AssessmentSubmission)
                .filter(
                    AssessmentSubmission.university_id == lecturer.university_id,
                    AssessmentSubmission.assessment_id == job.assessment_id,
                    AssessmentSubmission.id.in_(tracked_submission_ids),
                )
                .order_by(AssessmentSubmission.id)
                .all()
            )

            result_submission_ids = {
                result.submission_id
                for result in results
            }

            for submission in submissions:
                if submission.id not in result_submission_ids and submission.student_id is None:
                    pending_submissions.append(
                        {
                            "submission_id": submission.id,
                            "file_name": submission.file_name,
                            "student_id": None,
                            "status": "pending_student_match",
                        }
                    )

    return {
        "job_id": job_id,
        "assessment_id": job.assessment_id,
        "status": job.status,
        "total_submissions": job.total_submissions,
        "processed_submissions": job.processed_submissions,
        "count": len(results),
        "pending_submissions": pending_submissions,
        "pending_submission_count": len(pending_submissions),
        "results": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "submission_id": r.submission_id,
                "question_id": r.question_id,
                "extracted_answer": r.extracted_answer,
                "suggested_score": r.suggested_score,
                "max_score": r.max_score,
                "confidence": r.confidence,
                "grading_evidence": r.grading_evidence,
                "feedback": r.feedback,
                "status": r.status,
                "lecturer_score": r.lecturer_score,
                "lecturer_comment": r.lecturer_comment,
                "reviewed_by": r.reviewed_by,
                "reviewed_at": r.reviewed_at,
            }
            for r in results
        ],
    }


# ============================================================
# MANUALLY MATCH ANSWER PAPER TO STUDENT
# ============================================================

@router.post("/submissions/{submission_id}/match-student")
def match_submission_to_student(
    submission_id: int,
    student_id: int,
    lecturer: Lecturer = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    submission = (
        db.query(AssessmentSubmission)
        .filter(
            AssessmentSubmission.id == submission_id,
            AssessmentSubmission.university_id == lecturer.university_id,
        )
        .first()
    )

    if not submission:
        raise HTTPException(
            status_code=404,
            detail="Answer paper submission not found.",
        )

    assessment, course = verify_ai_marking_access(
        db=db,
        lecturer=lecturer,
        assessment_id=submission.assessment_id,
        required_permission="can_manage_results",
    )

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id,
            Student.university_id == lecturer.university_id,
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    department_id = course.get("department_id")

    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    independent_mode = (
        department is not None
        and department.name.strip().casefold()
        == "independent department"
    )

    if not independent_mode:
        enrolled = verify_student_enrollment(
            db,
            student.id,
            assessment.course_offering_id,
        )

        if not enrolled:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This student is not enrolled in the course "
                    "for this assessment."
                ),
            )

    submission.student_id = student.id
    submission.status = "uploaded"

    updated_results = (
        db.query(AIMarkingResult)
        .filter(
            AIMarkingResult.submission_id == submission.id,
            AIMarkingResult.university_id == lecturer.university_id,
        )
        .all()
    )

    for result in updated_results:
        result.student_id = student.id
        if result.status in {"pending_student_match", "manual_review", "needs_review"}:
            result.status = "pending_review"

    db.commit()
    db.refresh(submission)

    return {
        "message": "Answer paper matched to student successfully.",
        "submission_id": submission.id,
        "student_id": student.id,
        "student_name": f"{student.first_name} {student.last_name}",
        "matric_number": student.matric_number,
        "status": submission.status,
        "updated_results": len(updated_results),
    }


# ============================================================
# REVIEW ONE AI MARKING RESULT
# ============================================================

@router.post(
    "/results/{result_id}/review"
)
@router.post(
    "/results/{result_id}/review"
)
def review_marking_result(
    result_id: int,
    approved: bool,
    lecturer_score: float | None = None,
    lecturer_comment: str | None = None,
    lecturer: Lecturer = Depends(require_lecturer),
    db: Session = Depends(get_db),
):
    result = (
        db.query(AIMarkingResult)
        .filter(
            AIMarkingResult.id == result_id,
            AIMarkingResult.university_id == lecturer.university_id,
        )
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="AI marking result not found.",
        )

    if result.status != "pending_review":
        raise HTTPException(
            status_code=400,
            detail="This marking result has already been reviewed.",
        )

    if result.student_id is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "This result has no identified student. "
                "Match the submission to a student before "
                "reviewing the AI marking."
            ),
        )

    job = (
        db.query(AIMarkingJob)
        .filter(
            AIMarkingJob.id == result.job_id,
            AIMarkingJob.university_id == lecturer.university_id,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="AI marking job not found.",
        )

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == job.assessment_id,
            Assessment.university_id == lecturer.university_id,
        )
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found.",
        )

    assessment, course = verify_ai_marking_access(
        db=db,
        lecturer=lecturer,
        assessment_id=assessment.id,
        required_permission="can_manage_results",
    )

    final_score = (
        lecturer_score
        if lecturer_score is not None
        else result.suggested_score
    )

    if final_score is None:
        raise HTTPException(
            status_code=400,
            detail="No score is available for approval.",
        )

    try:
        final_score = float(final_score)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Lecturer score must be a valid number.",
        )

    if final_score < 0:
        raise HTTPException(
            status_code=400,
            detail="Score cannot be negative.",
        )

    if final_score > result.max_score:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Score must be between 0 and "
                f"{result.max_score}."
            ),
        )

    result.reviewed_by = lecturer.id
    result.reviewed_at = datetime.now(timezone.utc)
    result.lecturer_score = final_score
    result.lecturer_comment = lecturer_comment

    if approved:
        result.status = "approved"
    else:
        result.status = "overridden"

    db.commit()
    db.refresh(result)

    student_results = (
        db.query(AIMarkingResult)
        .filter(
            AIMarkingResult.job_id == job.id,
            AIMarkingResult.university_id == lecturer.university_id,
            AIMarkingResult.student_id == result.student_id,
        )
        .order_by(AIMarkingResult.question_id)
        .all()
    )

    if not student_results:
        raise HTTPException(
            status_code=500,
            detail="No marking results found for this student.",
        )

    final_statuses = {
        "approved",
        "overridden",
    }

    all_reviewed = all(
        r.status in final_statuses
        for r in student_results
    )

    assessment_score_saved = False
    total_score = None

    if all_reviewed:

        missing_scores = [
            r.id
            for r in student_results
            if r.lecturer_score is None
        ]

        if missing_scores:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "All reviewed questions must "
                        "have a final lecturer score."
                    ),
                    "result_ids_missing_scores": missing_scores,
                },
            )

        total_score = sum(
            float(r.lecturer_score)
            for r in student_results
        )

        if total_score > assessment.max_score:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Calculated student score "
                        "exceeds the assessment maximum."
                    ),
                    "calculated_score": total_score,
                    "assessment_max_score": assessment.max_score,
                },
            )

        comments = []

        for r in student_results:
            if r.lecturer_comment:
                comment = r.lecturer_comment.strip()
                if comment:
                    comments.append(comment)

        combined_comment = (
            " | ".join(comments)
            if comments
            else None
        )

        save_student_score(
            db=db,
            university_id=lecturer.university_id,
            student_id=result.student_id,
            assessment_id=assessment.id,
            score=total_score,
            marked_by=lecturer.id,
            lecturer_comment=combined_comment,
            is_absent=False,
        )

        assessment_score_saved = True

    return {
        "result_id": result.id,
        "status": result.status,
        "question_score": final_score,
        "student_id": result.student_id,
        "job_id": job.id,
        "all_questions_reviewed": all_reviewed,
        "assessment_score_saved": assessment_score_saved,
        "assessment_score": total_score,
        "message": (
            "Question review saved."
            if not assessment_score_saved
            else "All questions reviewed. Final assessment score saved."
        ),
    }



