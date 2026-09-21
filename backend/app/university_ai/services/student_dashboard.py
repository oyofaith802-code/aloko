from __future__ import annotations

from sqlalchemy.orm import Session

from app.university_ai.models.people import Student
from app.university_ai.models.academic import CourseOffering, StudentCourse
from app.university_ai.models.assessment import ResultSheet
from app.university_ai.models.attendance import AttendanceRecord
from app.university_ai.models.clearance import StudentClearance, StudentClearanceStage
from app.university_ai.models.payment import PaymentInvoice, PaymentTransaction
from app.university_ai.models.academic import CourseOffering


def get_student_dashboard(
    db: Session,
    student: Student,
):
    enrollments = (
        db.query(StudentCourse, CourseOffering)
        .join(
            CourseOffering,
            CourseOffering.id == StudentCourse.course_offering_id,
        )
        .filter(
            StudentCourse.university_id == student.university_id,
            StudentCourse.student_id == student.id,
            StudentCourse.enrollment_status == "enrolled",
        )
        .all()
    )

    courses = []

    results = (
        db.query(ResultSheet)
        .filter(
            ResultSheet.university_id == student.university_id,
            ResultSheet.student_id == student.id,
        )
        .all()
    )
    attendance = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.university_id == student.university_id,
            AttendanceRecord.student_id == student.id,
        )
        .all()
    )
    clearances = (
        db.query(StudentClearance)
        .filter(
            StudentClearance.university_id == student.university_id,
            StudentClearance.student_id == student.id,
        )
        .all()
    )
    invoices = (
        db.query(PaymentInvoice)
        .filter(
            PaymentInvoice.university_id == student.university_id,
            PaymentInvoice.student_id == student.id,
        )
        .all()
    )
    transactions = (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.university_id == student.university_id,
            PaymentTransaction.student_id == student.id,
        )
        .all()
    )

    for enrollment, offering in enrollments:
        courses.append(
            {
                "enrollment_id": enrollment.id,
                "course_offering_id": offering.id,
                "course_id": offering.course_id,
                "session_id": offering.academic_session_id,
                "semester_id": offering.semester_id,
                "status": enrollment.enrollment_status,
            }
        )

    return {
        "student": {
            "id": student.id,
            "matric_number": student.matric_number,
            "first_name": student.first_name,
            "middle_name": student.middle_name,
            "last_name": student.last_name,
            "level": student.level,
            "status": student.status,
        },
        "courses": courses,
        "course_count": len(courses),
        "results": [
            {
                "id": result.id,
                "course_offering_id": result.course_offering_id,
                "total_score": result.total_score,
                "percentage": result.percentage,
                "grade": result.grade,
                "grade_point": result.grade_point,
                "credit_units": result.credit_units,
                "remarks": result.remarks,
                "status": result.status,
            }
            for result in results
        ],
        "result_count": len(results),
        "attendance": [
            {
                "id": record.id,
                "course_offering_id": record.course_offering_id,
                "attendance_date": record.attendance_date,
                "status": record.status,
                "note": record.note,
            }
            for record in attendance
        ],
        "attendance_count": len(attendance),
        "clearances": [
            {
                "id": clearance.id,
                "academic_session_id": clearance.academic_session_id,
                "clearance_type": clearance.clearance_type,
                "status": clearance.status,
                "payment_status": clearance.payment_status,
                "submitted_at": clearance.submitted_at,
                "completed_at": clearance.completed_at,
                "rejection_reason": clearance.rejection_reason,
            }
            for clearance in clearances
        ],
        "clearance_count": len(clearances),
        "payments": {
            "invoices": [
                {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "fee_id": invoice.fee_id,
                    "clearance_id": invoice.clearance_id,
                    "amount": invoice.amount,
                    "currency": invoice.currency,
                    "status": invoice.status,
                    "due_date": invoice.due_date,
                    "created_at": invoice.created_at,
                }
                for invoice in invoices
            ],
            "transactions": [
                {
                    "id": transaction.id,
                    "invoice_id": transaction.invoice_id,
                    "provider": transaction.provider,
                    "transaction_reference": transaction.transaction_reference,
                    "amount": transaction.amount,
                    "currency": transaction.currency,
                    "status": transaction.status,
                    "paid_at": transaction.paid_at,
                    "created_at": transaction.created_at,
                }
                for transaction in transactions
            ],
            "invoice_count": len(invoices),
            "transaction_count": len(transactions),
        },
    }
