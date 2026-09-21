# ============================================================
# ALOKO UNIVERSITY AI MODELS
# ============================================================

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

from app.university_ai.models.portal import (
    UniversityPortalConfig,
    UniversityPortalSync,
    UniversityPortalMapping,
    UniversityPortalWebhook,
    UniversityPortalIntegrationLog,
)
from app.university_ai.models.ai_marking import (
    AssessmentQuestion,
    AssessmentSubmission,
    AIMarkingJob,
    AIMarkingResult,
)
from app.university_ai.models.course_document import (
    CourseDocument,
)
from app.university_ai.models.student_invitation import StudentInvitation
