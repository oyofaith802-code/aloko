from app.database.connection import Base, engine

# Import every university model so SQLAlchemy knows about the tables.
from app.university_ai.models.university import (
    University,
    Faculty,
    Department,
    Programme,
    Course,
    AcademicSession,
    AcademicSemester,
    UniversityMembership,
)

from app.university_ai.models.people import (
    Student,
    Lecturer,
)

from app.university_ai.models.academic import (
    UniversityClass,
    CourseOffering,
    LecturerCourse,
    StudentCourse,
)

from app.university_ai.models.assessment import (
    Assessment,
    StudentScore,
    ResultSheet,
)

from app.university_ai.models.attendance import (
    AttendanceRecord,
)

from app.university_ai.services.result_audit import (
    ResultCorrectionAudit,
)

from app.university_ai.models.clearance import (
    ClearanceConfiguration,
    ClearanceStage,
    ClearanceRequirement,
    StudentClearance,
    StudentClearanceStage,
    ClearanceAudit,
)

from app.university_ai.models.payment import (
    UniversityPaymentConfig,
    UniversityFee,
    PaymentInvoice,
    PaymentTransaction,
    PaymentVerification,
    PaymentWebhook,
)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

    print("UNIVERSITY CLEARANCE + PAYMENT TABLES CREATED")
    print("PHASE 8.5F DATABASE FOUNDATION OK")