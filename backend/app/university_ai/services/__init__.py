# ============================================================
# ALOKO UNIVERSITY AI SERVICES
# ============================================================

# ------------------------------------------------------------
# Student Import
# ------------------------------------------------------------

from app.university_ai.services.student_importer import (
    read_student_file,
    detect_columns,
    validate_student_rows,
    preview_student_import,
    import_students,
    process_student_import,
)

# ------------------------------------------------------------
# Score Import
# ------------------------------------------------------------

from app.university_ai.services.score_importer import (
    read_score_file,
    detect_matric_column,
    detect_assessment_columns,
    preview_score_import,
    import_scores,
    process_score_import,
)

# ------------------------------------------------------------
# Result Engine
# ------------------------------------------------------------

from app.university_ai.services.result_engine import (
    get_grade,
    get_course_assessments,
    get_student_scores,
    validate_assessment_weights,
    calculate_student_result,
    generate_result_sheet,
    generate_course_results,
    approve_result,
    publish_result,
    get_student_result,
)

# ------------------------------------------------------------
# GPA / CGPA Engine
# ------------------------------------------------------------

from app.university_ai.services.gpa_engine import (
    validate_grade_point,
    validate_credit_units,
    calculate_gpa_from_results,
    calculate_semester_gpa,
    calculate_cgpa,
    get_academic_standing,
    get_academic_summary,
    get_result_summary,
)

# ------------------------------------------------------------
# Lecturer AI
# ------------------------------------------------------------

from app.university_ai.services.lecturer_ai import (
    get_lecturer_profile,
    get_lecturer_courses,
    get_course_students,
    get_course_assessments_for_lecturer,
    get_course_score_summary,
    get_lecturer_dashboard,
)

# ------------------------------------------------------------
# Lecturer Assessment Management
# ------------------------------------------------------------

from app.university_ai.services.lecturer_assessment import (
    validate_assessment_type,
    validate_max_score,
    validate_weight,
    validate_score,
    create_assessment,
    update_assessment,
    deactivate_assessment,
    list_assessments,
    validate_course_assessments,
    save_student_score,
    get_score_completion,
    get_missing_scores,
    compile_course_scores,
)

# ------------------------------------------------------------
# Lecturer Analytics
# ------------------------------------------------------------

from app.university_ai.services.lecturer_analytics import (
    get_class_performance,
    get_score_distribution,
    get_student_performance,
    analyze_student_strengths,
    get_at_risk_students,
    generate_student_remark,
    generate_class_remarks,
    generate_lecturer_course_report,
)
from app.university_ai.services.payment import (
    create_payment_config,
    get_payment_config,
    update_payment_config,
    create_university_fee,
    list_university_fees,
    deactivate_university_fee,
    create_payment_invoice,
    get_invoice,
    get_student_invoices,
    create_payment_transaction,
    get_transaction,
    update_transaction_status,
    create_payment_verification,
    verify_payment,
    reject_payment,
    record_payment_webhook,
    mark_webhook_processed,
    mark_clearance_payment_verified,
    get_payment_summary,
)

# ------------------------------------------------------------
# Attendance
# ------------------------------------------------------------

from app.university_ai.services.attendance import (
    validate_attendance_status,
    mark_attendance,
    bulk_mark_attendance,
    update_attendance,
    get_student_attendance_history,
    calculate_attendance_percentage,
    get_course_attendance_summary,
    get_low_attendance_students,
    generate_lecturer_attendance_report,
)

# ------------------------------------------------------------
# Result Correction + Audit
# ------------------------------------------------------------

from app.university_ai.services.result_correction import (
    request_score_correction,
    approve_score_correction,
    reject_score_correction,
    get_result_correction_history,
    get_pending_corrections,
)

# ============================================================
# PUBLIC SERVICES
# ============================================================

__all__ = [

    # Student Import
    "read_student_file",
    "detect_columns",
    "validate_student_rows",
    "preview_student_import",
    "import_students",
    "process_student_import",

    # Score Import
    "read_score_file",
    "detect_matric_column",
    "detect_assessment_columns",
    "preview_score_import",
    "import_scores",
    "process_score_import",

    # Result Engine
    "get_grade",
    "get_course_assessments",
    "get_student_scores",
    "validate_assessment_weights",
    "calculate_student_result",
    "generate_result_sheet",
    "generate_course_results",
    "approve_result",
    "publish_result",
    "get_student_result",

    # GPA / CGPA
    "validate_grade_point",
    "validate_credit_units",
    "calculate_gpa_from_results",
    "calculate_semester_gpa",
    "calculate_cgpa",
    "get_academic_standing",
    "get_academic_summary",
    "get_result_summary",

    # Lecturer AI
    "get_lecturer_profile",
    "get_lecturer_courses",
    "get_course_students",
    "get_course_assessments_for_lecturer",
    "get_course_score_summary",
    "get_lecturer_dashboard",

    # Lecturer Assessment
    "validate_assessment_type",
    "validate_max_score",
    "validate_weight",
    "validate_score",
    "create_assessment",
    "update_assessment",
    "deactivate_assessment",
    "list_assessments",
    "validate_course_assessments",
    "save_student_score",
    "get_score_completion",
    "get_missing_scores",
    "compile_course_scores",

    # Lecturer Analytics
    "get_class_performance",
    "get_score_distribution",
    "get_student_performance",
    "analyze_student_strengths",
    "get_at_risk_students",
    "generate_student_remark",
    "generate_class_remarks",
    "generate_lecturer_course_report",

    # Attendance
    "validate_attendance_status",
    "mark_attendance",
    "bulk_mark_attendance",
    "update_attendance",
    "get_student_attendance_history",
    "calculate_attendance_percentage",
    "get_course_attendance_summary",
    "get_low_attendance_students",
    "generate_lecturer_attendance_report",

    # Result Correction + Audit
    "request_score_correction",
    "approve_score_correction",
    "reject_score_correction",
    "get_result_correction_history",
    "get_pending_corrections",
]

from app.university_ai.services.portal_integration import (
    validate_integration_type,
    validate_status,
    validate_sync_type,
    validate_sync_direction,
    mask_secret,
    serialize_portal_config,
    create_integration_log,
    get_integration_logs,
    create_portal_config,
    get_portal_config,
    list_portal_configs,
    update_portal_config,
    activate_portal,
    deactivate_portal,
    validate_portal_connection,
    create_sync_job,
    get_sync_job,
    list_sync_jobs,
    start_sync_job,
    complete_sync_job,
    fail_sync_job,
    create_portal_mapping,
    get_portal_mapping,
    get_mapping_by_aloko_id,
    list_portal_mappings,
    record_portal_webhook,
    get_portal_webhook,
    list_portal_webhooks,
    process_portal_webhook,
    get_portal_summary,
)