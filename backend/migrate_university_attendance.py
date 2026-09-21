from app.database.connection import engine, Base

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

from app.university_ai.models.attendance import AttendanceRecord


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

    print("UNIVERSITY ATTENDANCE TABLE CREATED")
    print("PHASE 8.5D MIGRATION OK")