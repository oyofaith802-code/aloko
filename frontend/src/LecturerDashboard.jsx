import { useEffect, useState } from "react";
import {
  getLecturerDashboard,
  getLecturerCourseStudents,
  getLecturerCourseAssessments,
  getLecturerCourseScores,
  downloadLecturerCourseResults,
  addLecturerStudent,
  previewLecturerStudentImport,
  importLecturerStudents,
  createLecturerAssessment,
  updateLecturerAssessment,
  deleteLecturerAssessment,
  saveLecturerStudentScore,
  getLecturerCourseAttendance,
  bulkMarkLecturerAttendance,
  getLecturerAttendanceReport,
  getLecturerLowAttendance,
  uploadQuestionPaper,
  uploadStudentAnswerPapers,
  runAIMarking,
  getAIMarkingResults,
  reviewAIMarkingResult,
  matchAIMarkingSubmission,
} from "./api";

export default function LecturerDashboard({ onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [courseDocuments, setCourseDocuments] = useState([]);
  const [courseDocumentsLoading, setCourseDocumentsLoading] = useState(false);
  const [courseDocumentFile, setCourseDocumentFile] = useState(null);
  const [courseDocumentTitle, setCourseDocumentTitle] = useState("");
  const [courseDocumentUploading, setCourseDocumentUploading] = useState(false);
  const [courseDocumentError, setCourseDocumentError] = useState("");
  const [courseDocumentMessage, setCourseDocumentMessage] = useState("");
  const [students, setStudents] = useState([]);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [studentsError, setStudentsError] = useState("");
  const [showAddStudentForm, setShowAddStudentForm] = useState(false);
  const [studentSaving, setStudentSaving] = useState(false);
  const [studentForm, setStudentForm] = useState({ matric_number: "", first_name: "", middle_name: "", last_name: "", level: "100", entry_year: "", graduation_year: "", phone: "" });
  const [assessments, setAssessments] = useState([]);
  const [assessmentsLoading, setAssessmentsLoading] = useState(false);
  const [assessmentsError, setAssessmentsError] = useState("");
  const [selectedPanel, setSelectedPanel] = useState("students");
  const [results, setResults] = useState(null);
  const [resultsLoading, setResultsLoading] = useState(false);
  const [resultsExporting, setResultsExporting] = useState(false);

  const [resultsError, setResultsError] = useState("");
  const [scoreSaving, setScoreSaving] = useState(false);
  const [attendance, setAttendance] = useState([]);
  const [attendanceLoading, setAttendanceLoading] = useState(false);
  const [attendanceError, setAttendanceError] = useState("");
  const [aiMarkingAssessment, setAIMarkingAssessment] = useState(null);
  const [aiQuestionFile, setAIQuestionFile] = useState(null);
  const [aiAnswerFiles, setAIAnswerFiles] = useState([]);
  const [aiUploadedSubmissionIds, setAIUploadedSubmissionIds] = useState([]);
  const [aiMarkingLoading, setAIMarkingLoading] = useState(false);
  const [aiMarkingUploading, setAIMarkingUploading] = useState(false);
  const [aiMarkingError, setAIMarkingError] = useState("");
  const [aiMarkingMessage, setAIMarkingMessage] = useState("");
const [aiDetectedQuestions, setAIDetectedQuestions] = useState([]);
const [aiQuestionMarks, setAIQuestionMarks] = useState({});
  const [aiMarkingJobId, setAIMarkingJobId] = useState(null);
  const [aiMarkingResults, setAIMarkingResults] = useState([]);
  const [aiPendingSubmissions, setAIPendingSubmissions] = useState([]);

  const [aiReviewingId, setAIReviewingId] = useState(null);
  const [aiReviewScores, setAIReviewScores] = useState({});
  const [aiReviewComments, setAIReviewComments] = useState({});
  const [aiMatchingStudentIds, setAIMatchingStudentIds] = useState({});
  const [aiMatchingId, setAIMatchingId] = useState(null);
  const [attendanceDate, setAttendanceDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [attendanceSaving, setAttendanceSaving] = useState(false);
  const [lowAttendance, setLowAttendance] = useState([]);
  const [lowAttendanceLoading, setLowAttendanceLoading] = useState(false);
  const [lowAttendanceError, setLowAttendanceError] = useState("");

  const [showAssessmentForm, setShowAssessmentForm] = useState(false);
  const [assessmentForm, setAssessmentForm] = useState({
    title: "",
    assessment_type: "ca",
    max_score: 100,
    weight: "",
    assessment_date: "",
    description: "",
  });
  const [assessmentSaving, setAssessmentSaving] = useState(false);
const [editingAssessmentId, setEditingAssessmentId] = useState(null);

const [studentImportFile, setStudentImportFile] = useState(null);
const [studentImportLoading, setStudentImportLoading] = useState(false);
const [studentImportError, setStudentImportError] = useState("");
const [studentImportMessage, setStudentImportMessage] = useState("");
const [studentImportPreview, setStudentImportPreview] = useState(null);
const [studentImportCommitting, setStudentImportCommitting] = useState(false);

const [studentSearch, setStudentSearch] = useState("");
const [studentStatusFilter, setStudentStatusFilter] = useState("all");

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const result = await getLecturerDashboard();
        if (mounted) setData(result);
      } catch (err) {
        if (mounted) setError(err?.message || "Unable to load lecturer dashboard.");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();

    return () => {
      mounted = false;
    };
  }, []);

  async function loadCourseDocuments(course) {
    if (!course?.course_offering_id) return;

    setCourseDocumentsLoading(true);
    setCourseDocumentError("");

    try {
      const result = await getLecturerCourseDocuments(
        course.course_offering_id
      );

      setCourseDocuments(
        Array.isArray(result)
          ? result
          : (result?.documents || result?.data || [])
      );
    } catch (err) {
      setCourseDocumentError(
        err?.message || "Unable to load course documents."
      );
    } finally {
      setCourseDocumentsLoading(false);
    }
  }

  async function openCourseDocuments(course) {
    setSelectedCourse(course);
    setSelectedPanel("documents");
    setCourseDocuments([]);
    setCourseDocumentError("");
    setCourseDocumentMessage("");
    setCourseDocumentFile(null);
    setCourseDocumentTitle("");
    await loadCourseDocuments(course);
  }

  async function uploadCourseDocument() {
    if (
      !selectedCourse ||
      !courseDocumentFile ||
      courseDocumentUploading
    ) {
      return;
    }

    setCourseDocumentUploading(true);
    setCourseDocumentError("");
    setCourseDocumentMessage("");

    try {
      const result = await uploadLecturerCourseDocument(
        selectedCourse.course_offering_id,
        courseDocumentFile,
        courseDocumentTitle
      );

      setCourseDocumentMessage(
        result?.message || "Course document uploaded successfully."
      );

      setCourseDocumentFile(null);
      setCourseDocumentTitle("");

      const fileInput = document.getElementById(
        "lecturer-course-document-file"
      );

      if (fileInput) {
        fileInput.value = "";
      }

      await loadCourseDocuments(selectedCourse);
    } catch (err) {
      setCourseDocumentError(
        err?.message || "Unable to upload course document."
      );
    } finally {
      setCourseDocumentUploading(false);
    }
  }

  async function openStudents(course) {
    setSelectedPanel("students");
    setSelectedCourse(course);
    setStudents([]);
    setStudentsError("");
    setStudentsLoading(true);
    try {
      const result = await getLecturerCourseStudents(course.course_offering_id);
      setStudents(Array.isArray(result) ? result : (result?.students || result?.data || []));
    } catch (err) {
      setStudentsError(err?.message || "Unable to load students.");
    } finally {
      setStudentsLoading(false);
    }
  }

  const filteredStudents = students.filter((student) => {
  const search = studentSearch.trim().toLowerCase();

  const name =
    student.name ||
    [student.first_name, student.middle_name, student.last_name]
      .filter(Boolean)
      .join(" ");

  const identifier =
    student.matric_number ||
    student.registration_number ||
    student.student_number ||
    "";

  const matchesSearch =
    !search ||
    name.toLowerCase().includes(search) ||
    String(identifier).toLowerCase().includes(search);

  const status = String(student.status || "active").toLowerCase();

  return (
    matchesSearch &&
    (studentStatusFilter === "all" ||
      status === studentStatusFilter.toLowerCase())
  );
});

async function saveStudent() {
    if (!selectedCourse || studentSaving) return;
    if (!studentForm.matric_number.trim() || !studentForm.first_name.trim() || !studentForm.last_name.trim()) {
      setStudentsError("Matric number, first name, and last name are required.");
      return;
    }
    setStudentSaving(true);
    setStudentsError("");
    try {
      await addLecturerStudent(selectedCourse.course_offering_id, { matric_number: studentForm.matric_number.trim(), first_name: studentForm.first_name.trim(), middle_name: studentForm.middle_name.trim() || null, last_name: studentForm.last_name.trim(), level: studentForm.level.trim() || null, entry_year: studentForm.entry_year === "" ? null : Number(studentForm.entry_year), graduation_year: studentForm.graduation_year === "" ? null : Number(studentForm.graduation_year), phone: studentForm.phone.trim() || null });
      setStudentForm({ matric_number: "", first_name: "", middle_name: "", last_name: "", level: "100", entry_year: "", graduation_year: "", phone: "" });
      setShowAddStudentForm(false);
      await openStudents(selectedCourse);
    } catch (err) {
      setStudentsError(err?.message || "Unable to add student.");
    } finally {
      setStudentSaving(false);
    }
  }

  async function previewStudentImportFile() {
    if (!selectedCourse || !studentImportFile || studentImportLoading) return;
    setStudentImportLoading(true);
    setStudentImportError('');
    setStudentImportMessage('');
    setStudentImportPreview(null);
    try {
      const result = await previewLecturerStudentImport(selectedCourse.course_offering_id, studentImportFile);
      setStudentImportPreview(result);
    } catch (err) {
      setStudentImportError(err?.message || 'Unable to preview student import.');
    } finally {
      setStudentImportLoading(false);
    }
  }

  async function commitStudentImport() {
    if (!selectedCourse || !studentImportFile || !studentImportPreview || studentImportCommitting) return;
    if (studentImportPreview?.validation?.valid === false) {
      setStudentImportError('Fix the validation errors before importing students.');
      return;
    }
    setStudentImportCommitting(true);
    setStudentImportError('');
    setStudentImportMessage('');
    try {
      const result = await importLecturerStudents(selectedCourse.course_offering_id, studentImportFile, true);
      setStudentImportMessage(result?.message || 'Student import completed.');
      setStudentImportFile(null);
      setStudentImportPreview(null);
      const fileInput = document.getElementById('lecturer-student-import-file');
      if (fileInput) fileInput.value = '';
      await openStudents(selectedCourse);
    } catch (err) {
      setStudentImportError(err?.message || 'Unable to import students.');
    } finally {
      setStudentImportCommitting(false);
    }
  }

  async function openAssessments(course) {
    setSelectedPanel("assessments");
    setSelectedCourse(course);
    setAssessments([]);
    setAssessmentsError("");
    setAssessmentsLoading(true);
    try {
      const result = await getLecturerCourseAssessments(course.course_offering_id);
      setAssessments(Array.isArray(result) ? result : (result?.assessments || result?.data || []));
    } catch (err) {
      setAssessmentsError(err?.message || "Unable to load assessments.");
    } finally {
      setAssessmentsLoading(false);
    }
  }

  async function openAIMarking(course, assessment = null) {
  setSelectedCourse(course);
  setSelectedPanel("ai-marking");

  setAIMarkingAssessment(null);
  setAIQuestionFile(null);
  setAIDetectedQuestions([]);
  setAIQuestionMarks({});
  setAIAnswerFiles([]);
  setAIUploadedSubmissionIds([]);
  setAIMarkingError("");
  setAIMarkingMessage("");
  setAIMarkingJobId(null);
  setAIMarkingResults([]);
  setAIReviewScores({});
  setAIReviewComments({});
  setAIMatchingStudentIds({});
  setAIMatchingId(null);

  try {
    setAssessmentsLoading(true);
    setAssessmentsError("");

    console.log(
      "AI MARKING COURSE FULL:",
      JSON.stringify(course, null, 2)
    );
    console.log(
      "AI MARKING COURSE OFFERING ID:",
      course.course_offering_id
    );

    const result = await getLecturerCourseAssessments(
      course.course_offering_id
    );

    console.log(
      "AI MARKING REQUEST FINISHED FOR OFFERING:",
      course.course_offering_id
    );

    console.log("AI MARKING RAW ASSESSMENTS JSON:", JSON.stringify(result, null, 2));

    const loadedAssessments = Array.isArray(result)
      ? result
      : Array.isArray(result?.assessments)
        ? result.assessments
        : Array.isArray(result?.data)
          ? result.data
          : [];

    console.log("AI MARKING LOADED ASSESSMENTS:", loadedAssessments);

    setAssessments(loadedAssessments);

    const studentResult = await getLecturerCourseStudents(
      course.course_offering_id
    );

    const loadedStudents = Array.isArray(studentResult)
      ? studentResult
      : Array.isArray(studentResult?.students)
        ? studentResult.students
        : Array.isArray(studentResult?.data)
          ? studentResult.data
          : [];

    console.log("AI MARKING LOADED STUDENTS:", loadedStudents);

    setStudents(loadedStudents);

    if (!loadedAssessments.length) {
      setAIMarkingError(
        "No active assessments were found for this course."
      );
      return;
    }

    let selectedAssessment = null;

    if (assessment?.id != null) {
      selectedAssessment =
        loadedAssessments.find(
          (item) => String(item.id) === String(assessment.id)
        ) || null;
    }

    if (!selectedAssessment) {
      selectedAssessment = loadedAssessments[0];
    }

    setAIMarkingAssessment(selectedAssessment);
  } catch (err) {
    setAIMarkingError(
      err?.message || "Unable to load assessments."
    );
  } finally {
    setAssessmentsLoading(false);
  }
}

  function getAIUniversityId() {
    return (
      data?.university_id ||
      data?.university?.id ||
      lecturer?.university_id ||
      selectedCourse?.university_id ||
      null
    );
  }

  async function uploadAIQuestionPaper() {
    if (!selectedCourse || !aiMarkingAssessment || !aiQuestionFile) {
      setAIMarkingError(
        "Select an assessment and question paper first."
      );
      return;
    }

    const universityId = getAIUniversityId();

    if (!universityId) {
      setAIMarkingError(
        "University ID is missing from the lecturer dashboard."
      );
      return;
    }

    setAIMarkingUploading(true);
    setAIMarkingError("");
    setAIMarkingMessage("");

    try {
      const result = await uploadQuestionPaper(
        aiMarkingAssessment.id,
        universityId,
        aiQuestionFile
      );

      const detectedQuestions = Array.isArray(result?.questions)
        ? result.questions
        : [];

      setAIDetectedQuestions(detectedQuestions);

      setAIQuestionMarks(
        detectedQuestions.reduce((marks, question) => {
          marks[question.id || question.question_number] =
            question.max_score ?? "";
          return marks;
        }, {})
      );
      setAIMarkingMessage(
        result?.message ||
        `Question paper uploaded successfully.${
          result?.question_count
            ? ` ${result.question_count} questions detected.`
            : ""
        }`
      );
    } catch (err) {
      setAIMarkingError(
        err?.message || "Unable to upload question paper."
      );
    } finally {
      setAIMarkingUploading(false);
    }
  }

  async function uploadAIAnswerPapers() {
    if (!selectedCourse || !aiMarkingAssessment) {
      setAIMarkingError("Select an assessment first.");
      return;
    }

    if (!aiAnswerFiles.length) {
      setAIMarkingError(
        "Select at least one student answer paper."
      );
      return;
    }

    const universityId = getAIUniversityId();

    if (!universityId) {
      setAIMarkingError(
        "University ID is missing from the lecturer dashboard."
      );
      return;
    }

    setAIMarkingUploading(true);
    setAIMarkingError("");
    setAIMarkingMessage("");

    try {
      const result = await uploadStudentAnswerPapers(
        aiMarkingAssessment.id,
        universityId,
        aiAnswerFiles
      );

      const uploadedResults = Array.isArray(result?.results)
        ? result.results
        : [];

      const submissionIds = uploadedResults
        .map((item) => Number(item?.submission_id))
        .filter((id) => Number.isFinite(id) && id > 0);

      if (!submissionIds.length) {
        throw new Error(
          "The answer papers were uploaded, but no submission IDs were returned."
        );
      }

      setAIUploadedSubmissionIds(submissionIds);

      setAIMarkingMessage(
        result?.message ||
        `${submissionIds.length} answer paper(s) uploaded successfully.`
      );
    } catch (err) {
      setAIMarkingError(
        err?.message || "Unable to upload student answer papers."
      );
    } finally {
      setAIMarkingUploading(false);
    }
  }

  async function startAIMarking() {
    if (!selectedCourse || !aiMarkingAssessment) {
      setAIMarkingError("Select an assessment first.");
      return;
    }

    const universityId = getAIUniversityId();

    if (!universityId) {
      setAIMarkingError(
        "University ID is missing from the lecturer dashboard."
      );
      return;
    }

    if (!aiUploadedSubmissionIds.length) {
      setAIMarkingError(
        "Upload student answer papers before starting AI marking."
      );
      return;
    }

    setAIMarkingLoading(true);
    setAIMarkingError("");
    setAIMarkingMessage("");

    try {
      const result = await runAIMarking(
        aiMarkingAssessment.id,
        universityId,
        aiUploadedSubmissionIds
      );

      setAIMarkingJobId(result?.job_id || null);

      setAIMarkingMessage(
        result?.message ||
        "AI marking completed successfully."
      );

      if (result?.job_id) {
        await loadAIMarkingResults(result.job_id);
      }
    } catch (err) {
      setAIMarkingError(
        err?.message || "Unable to run AI marking."
      );
    } finally {
      setAIMarkingLoading(false);
    }
  }

  async function loadAIMarkingResults(jobId = aiMarkingJobId) {
    if (!jobId) {
      setAIMarkingError("No AI marking job is available.");
      return;
    }

    const universityId = getAIUniversityId();

    if (!universityId) {
      setAIMarkingError(
        "University ID is missing from the lecturer dashboard."
      );
      return;
    }

    setAIMarkingLoading(true);
    setAIMarkingError("");

    try {
      const result = await getAIMarkingResults(
        jobId,
        universityId
      );

      const rows = Array.isArray(result)
        ? result
        : (result?.results || result?.data || []);

      setAIMarkingResults(rows);
      setAIPendingSubmissions(
        Array.isArray(result?.pending_submissions)
          ? result.pending_submissions
          : []
      );

      setAIReviewScores((previous) => {
        const next = { ...previous };

        rows.forEach((row) => {
          if (
            next[row.id] === undefined &&
            row.suggested_score !== undefined
          ) {
            next[row.id] = row.suggested_score;
          }
        });

        return next;
      });
    } catch (err) {
      setAIMarkingError(
        err?.message || "Unable to load AI marking results."
      );
    } finally {
      setAIMarkingLoading(false);
    }
  }

  async function matchAIStudent(result) {
    const universityId = getAIUniversityId();
    const studentId = aiMatchingStudentIds[result.submission_id];

    if (!universityId) {
      setAIMarkingError("University ID is missing from the lecturer dashboard.");
      return;
    }

    if (!result.submission_id) {
      setAIMarkingError("This AI result has no submission ID.");
      return;
    }

    if (!studentId) {
      setAIMarkingError("Select a student before matching the answer paper.");
      return;
    }

    setAIMatchingId(result.submission_id);
    setAIMarkingError("");
    setAIMarkingMessage("");

    try {
      const response = await matchAIMarkingSubmission(
        result.submission_id,
        universityId,
        Number(studentId)
      );

      setAIMarkingMessage(
        response?.message || "Answer paper matched to student successfully."
      );

      setAIMatchingStudentIds((previous) => {
        const next = { ...previous };
        delete next[result.submission_id];
        return next;
      });

      await loadAIMarkingResults(aiMarkingJobId);
    } catch (err) {
      setAIMarkingError(
        err?.message || "Unable to match answer paper to student."
      );
    } finally {
      setAIMatchingId(null);
    }
  }

  async function reviewAIResult(result, approved) {
    const universityId = getAIUniversityId();
    const lecturerId = lecturer?.id;

    if (!universityId || !lecturerId) {
      setAIMarkingError(
        "University or lecturer identity is missing."
      );
      return;
    }

    setAIReviewingId(result.id);
    setAIMarkingError("");

    try {
      await reviewAIMarkingResult(
        result.id,
        {
          universityId,
          lecturerId,
          approved,
          lecturerScore:
            aiReviewScores[result.id] !== undefined
              ? Number(aiReviewScores[result.id])
              : result.suggested_score,
          lecturerComment:
            aiReviewComments[result.id] || "",
        }
      );

      setAIMarkingMessage(
        approved
          ? "AI suggestion approved."
          : "AI marking reviewed and overridden."
      );

      await loadAIMarkingResults(aiMarkingJobId);
    } catch (err) {
      setAIMarkingError(
        err?.message || "Unable to review AI marking result."
      );
    } finally {
      setAIReviewingId(null);
    }
  }

  async function saveAssessment() {
  if (!selectedCourse || assessmentSaving) return;

  setAssessmentSaving(true);
  setAssessmentsError("");

  try {
    if (editingAssessmentId) {
      await updateLecturerAssessment(
        selectedCourse.course_offering_id,
        editingAssessmentId,
        {
          title: assessmentForm.title,
          assessment_type: assessmentForm.assessment_type,
          max_score: Number(assessmentForm.max_score),
          weight:
            assessmentForm.weight === ""
              ? null
              : Number(assessmentForm.weight),
          description: assessmentForm.description,
          assessment_date: assessmentForm.assessment_date || null,
        }
      );
    } else {
      await createLecturerAssessment(
        selectedCourse.course_offering_id,
        {
          title: assessmentForm.title,
          assessment_type: assessmentForm.assessment_type,
          max_score: Number(assessmentForm.max_score),
          weight:
            assessmentForm.weight === ""
              ? null
              : Number(assessmentForm.weight),
          description: assessmentForm.description,
          assessment_date: assessmentForm.assessment_date || null,
        }
      );
    }

    setAssessmentForm({
      title: "",
      assessment_type: "ca",
      max_score: 100,
      weight: "",
      description: "",
    });

    setEditingAssessmentId(null);
    setShowAssessmentForm(false);

    await openAssessments(selectedCourse);
  } catch (err) {
    setAssessmentsError(
      err?.message ||
        (editingAssessmentId
          ? "Unable to update assessment."
          : "Unable to create assessment.")
    );
  } finally {
    setAssessmentSaving(false);
  }
}

async function deleteAssessment(assessment) {
  if (!selectedCourse || assessmentSaving) return;

  const assessmentId = assessment?.id || assessment?.assessment_id;

  if (!assessmentId) {
    setAssessmentsError("Assessment ID is missing.");
    return;
  }

  const confirmed = window.confirm(
    `Delete "${assessment.title || assessment.name || "this assessment"}"? This action cannot be undone.`
  );

  if (!confirmed) return;

  setAssessmentSaving(true);
  setAssessmentsError("");

  try {
    await deleteLecturerAssessment(
      selectedCourse.course_offering_id,
      assessmentId
    );

    if (editingAssessmentId === assessmentId) {
      setEditingAssessmentId(null);
      setShowAssessmentForm(false);
    }

    await openAssessments(selectedCourse);
  } catch (err) {
    setAssessmentsError(
      err?.message || "Unable to delete assessment."
    );
  } finally {
    setAssessmentSaving(false);
  }
}

function startEditAssessment(assessment) {
  setEditingAssessmentId(
    assessment?.id || assessment?.assessment_id || null
  );

  setAssessmentForm({
    title:
      assessment?.title ||
      assessment?.name ||
      assessment?.assessment_name ||
      "",
    assessment_type:
      assessment?.assessment_type ||
      assessment?.type ||
      "ca",
    max_score:
      assessment?.max_score ??
      assessment?.total_marks ??
      100,
    weight: assessment?.weight ?? "",
    assessment_date: assessment?.assessment_date
      ? new Date(assessment.assessment_date).toISOString().slice(0, 10)
      : "",
    description: assessment?.description || "",
  });

  setShowAssessmentForm(true);
}

  async function openAttendance(course) {
    setSelectedCourse(course);
    setSelectedPanel("attendance");
    setAttendance([]);
    setAttendanceError("");
    setAttendanceLoading(true);

    try {
      const result = await getLecturerCourseAttendance(course.course_offering_id);
      setAttendance(Array.isArray(result) ? result : (result?.students || result?.data || []));
    } catch (err) {
      setAttendanceError(err?.message || "Unable to load attendance.");
    } finally {
      setAttendanceLoading(false);
    }
  }

  async function loadLowAttendance() {
    if (!selectedCourse || lowAttendanceLoading) return;

    setLowAttendanceLoading(true);
    setLowAttendanceError("");

    try {
      const result = await getLecturerLowAttendance(
        selectedCourse.course_offering_id
      );

      setLowAttendance(
        Array.isArray(result)
          ? result
          : (result?.students || result?.data || result?.low_attendance || [])
      );
    } catch (err) {
      setLowAttendanceError(
        err?.message || "Unable to load low-attendance report."
      );
    } finally {
      setLowAttendanceLoading(false);
    }
  }

  async function saveAttendance() {
    if (!selectedCourse || attendanceSaving) return;

    setAttendanceSaving(true);
    setAttendanceError("");

    try {
      const records = attendance.map((student) => ({
        student_id: student.student_id,
        status: student.status || "present",
        note: student.note || null,
      }));

      if (!records.length) {
        throw new Error("No students available for attendance.");
      }

      await bulkMarkLecturerAttendance(
        selectedCourse.course_offering_id,
        {
          attendance_date: attendanceDate,
          records,
        }
      );

      const refreshed = await getLecturerCourseAttendance(
        selectedCourse.course_offering_id
      );

      setAttendance(
        Array.isArray(refreshed)
          ? refreshed
          : (refreshed?.students || refreshed?.data || [])
      );
    } catch (err) {
      setAttendanceError(err?.message || "Unable to save attendance.");
    } finally {
      setAttendanceSaving(false);
    }
  }

  const courseDocumentsPanel =
    selectedPanel === "documents" && selectedCourse ? (
      <section className="lecturer-card">
        <div className="lecturer-section-header">
          <div>
            <h2>Course Knowledge Base</h2>
            <p>
              {selectedCourse.course_code || "Course"}  - {" "}
              {selectedCourse.course_name || "Selected Course"}
            </p>
          </div>

          <button
            className="lecturer-action secondary"
            type="button"
            onClick={() => {
              setSelectedPanel("students");
              setSelectedCourse(null);
            }}
          >
            ? Back to Courses
          </button>
        </div>

        <div
          style={{
            padding: 16,
            border: "1px solid rgba(148, 163, 184, 0.25)",
            borderRadius: 12,
            marginBottom: 18,
          }}
        >
          <h3 style={{ marginTop: 0 }}>
            Upload Course Material
          </h3>

          <p style={{ marginTop: 0, opacity: 0.75 }}>
            Upload textbooks, lecture notes, past questions, or other
            course documents. Aloko will process the material for the
            course knowledge base.
          </p>

          <div
            style={{
              display: "grid",
              gap: 12,
              maxWidth: 700,
            }}
          >
            <input
              type="text"
              placeholder="Document title (optional)"
              value={courseDocumentTitle}
              onChange={(e) =>
                setCourseDocumentTitle(e.target.value)
              }
            />

            <input
              id="lecturer-course-document-file"
              type="file"
              accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.webp,.heic,.heif"
              onChange={(e) =>
                setCourseDocumentFile(e.target.files?.[0] || null)
              }
            />

            <button
              className="lecturer-action"
              type="button"
              disabled={
                !courseDocumentFile ||
                courseDocumentUploading
              }
              onClick={uploadCourseDocument}
            >
              {courseDocumentUploading
                ? "Processing..."
                : "Upload Course Material"}
            </button>
          </div>

          {courseDocumentMessage && (
            <div
              style={{
                marginTop: 12,
                padding: 10,
                borderRadius: 8,
                background: "rgba(34, 197, 94, 0.1)",
              }}
            >
              {courseDocumentMessage}
            </div>
          )}

          {courseDocumentError && (
            <div
              style={{
                marginTop: 12,
                padding: 10,
                borderRadius: 8,
                background: "rgba(239, 68, 68, 0.1)",
              }}
            >
              {courseDocumentError}
            </div>
          )}
        </div>

        <div className="lecturer-section-header">
          <div>
            <h3>Course Materials</h3>
            <p>
              Documents already uploaded for this course.
            </p>
          </div>

          <button
            className="lecturer-action secondary"
            type="button"
            disabled={courseDocumentsLoading}
            onClick={() => loadCourseDocuments(selectedCourse)}
          >
            {courseDocumentsLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {courseDocumentsLoading ? (
          <div className="lecturer-loading">
            Loading course materials...
          </div>
        ) : courseDocuments.length === 0 ? (
          <div className="lecturer-empty">
            No course materials uploaded yet.
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gap: 12,
            }}
          >
            {courseDocuments.map((document) => (
              <div
                key={document.id}
                style={{
                  padding: 14,
                  border: "1px solid rgba(148, 163, 184, 0.25)",
                  borderRadius: 10,
                }}
              >
                <strong>
                  {document.title || document.original_filename}
                </strong>

                <div
                  style={{
                    marginTop: 6,
                    opacity: 0.75,
                    fontSize: 14,
                  }}
                >
                  {document.original_filename}
                  {"  -  "}
                  {String(document.file_type || "")
                    .replace(".", "")
                    .toUpperCase()}
                  {"  -  "}
                  {document.status || "uploaded"}
                  {"  -  "}
                  {document.text_length ?? 0} characters extracted
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    ) : null;

  const attendancePanel = selectedPanel === "attendance" && selectedCourse ? (
    <section className="lecturer-panel">
      <div className="lecturer-panel-header">
        <div>
          <h2>Attendance</h2>
          <p>
            {selectedCourse.course_code || "Course"}  - {" "}
            {selectedCourse.course_name || "Selected Course"}
          </p>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            className="lecturer-action secondary"
            type="button"
            onClick={() => setSelectedPanel("students")}
          >
            Back Ã‚Â¢-Back Ã‚Â Back
          </button>

          <button
            className="lecturer-action"
            type="button"
            onClick={saveAttendance}
            disabled={attendanceSaving || attendanceLoading}
          >
            {attendanceSaving ? "Saving..." : "Save Attendance"}
          </button>

          <button
            className="lecturer-action secondary"
            type="button"
            onClick={loadLowAttendance}
            disabled={lowAttendanceLoading}
          >
            {lowAttendanceLoading
              ? "Loading Report..."
              : "Low Attendance Report"}
          </button>
        </div>
      </div>

      <div style={{ marginBottom: 18 }}>
        <label style={{ display: "block", marginBottom: 6, fontWeight: 600 }}>
          Attendance Date
        </label>

        <input
          type="date"
          value={attendanceDate}
          onChange={(e) => setAttendanceDate(e.target.value)}
        />
      </div>

      {attendanceLoading && (
        <div className="lecturer-empty">Loading attendance...</div>
      )}

      {attendanceError && (
        <div className="lecturer-error">{attendanceError}</div>
      )}

      {!attendanceLoading && !attendanceError && attendance.length === 0 && (
        <div className="lecturer-empty">
          No students are enrolled in this course.
        </div>
      )}

      {lowAttendanceError && (
        <div className="lecturer-error" style={{ marginBottom: 16 }}>
          {lowAttendanceError}
        </div>
      )}

      {lowAttendance.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 12,
              marginBottom: 12,
              flexWrap: "wrap",
            }}
          >
            <div>
              <h3 style={{ margin: 0 }}>Low Attendance Report</h3>
              <p style={{ margin: "4px 0 0", opacity: 0.7 }}>
                Students currently below the attendance threshold.
              </p>
            </div>

            <button
              className="lecturer-action secondary"
              type="button"
              onClick={loadLowAttendance}
              disabled={lowAttendanceLoading}
            >
              {lowAttendanceLoading ? "Refreshing..." : "Refresh Report"}
            </button>
          </div>

          <div className="lecturer-results-table-wrap">
            <table className="lecturer-results-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Matric Number</th>
                  <th>Attendance</th>
                  <th>Present</th>
                  <th>Absent</th>
                  <th>Late</th>
                </tr>
              </thead>

              <tbody>
                {lowAttendance.map((student, index) => (
                  <tr
                    key={
                      student.student_id ??
                      student.id ??
                      student.matric_number ??
                      index
                    }
                  >
                    <td>
                      <strong>
                        {student.name ||
                          student.student_name ||
                          "Student"}
                      </strong>
                    </td>

                    <td>
                      {student.matric_number ||
                        student.registration_number ||
                        "-"}
                    </td>

                    <td>
                      <strong>
                        {Number(
                          student.attendance_percentage ??
                            student.attendance_percent ??
                            student.percentage ??
                            0
                        ).toFixed(1)}
                        %
                      </strong>
                    </td>

                    <td>{student.present ?? 0}</td>
                    <td>{student.absent ?? 0}</td>
                    <td>{student.late ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!attendanceLoading && attendance.length > 0 && (
        <div className="lecturer-results-table-wrap">
          <table className="lecturer-results-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Matric Number</th>
                <th>Attendance</th>
                <th>Status</th>
                    <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {attendance.map((student) => (
                <tr key={student.student_id}>
                  <td>
                    <strong>{student.name || "Student"}</strong>
                  </td>

                  <td>{student.matric_number || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>

                  <td>
                    <strong>
                      {Number(student.attendance_percentage || 0).toFixed(1)}%
                    </strong>
                    <small style={{ display: "block" }}>
                      {student.present || 0} present  - {" "}
                      {student.absent || 0} absent  - {" "}
                      {student.late || 0} late
                    </small>
                  </td>

                  <td>
                    <select
                      value={student.status || "present"}
                      onChange={(e) =>
                        setAttendance((current) =>
                          current.map((item) =>
                            item.student_id === student.student_id
                              ? { ...item, status: e.target.value }
                              : item
                          )
                        )
                      }
                    >
                      <option value="present">Present</option>
                      <option value="absent">Absent</option>
                      <option value="late">Late</option>
                      <option value="excused">Excused</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  ) : null;

  const openResults = async (course) => {
    setSelectedCourse(course);
    setSelectedPanel("results");
    setResults(null);
    setResultsError("");
    setResultsLoading(true);
    try {
      const result = await getLecturerCourseScores(course.course_offering_id);
      setResults(result);
    } catch (err) {
      setResultsError(err?.message || "Unable to load results.");
    } finally {
      setResultsLoading(false);
    }
  };

  const saveScore = async (payload) => {
    if (scoreSaving || !selectedCourse) return;
    setScoreSaving(true);
    setResultsError("");
    try {
      await saveLecturerStudentScore(selectedCourse.course_offering_id, { ...payload, score: payload.score === "" ? null : Number(payload.score) });
      const refreshed = await getLecturerCourseScores(selectedCourse.course_offering_id);
      setResults(refreshed);
    } catch (err) {
      setResultsError(err?.message || "Unable to save score.");
    } finally {
      setScoreSaving(false);
    }
  };

  
const exportResults = async (format) => {
  if (!selectedCourse?.course_offering_id) {
    setResultsError("No course selected for export.");
    return;
  }

  try {
    setResultsExporting(true);
    setResultsError("");

    await downloadLecturerCourseResults(
      selectedCourse.course_offering_id,
      format
    );
  } catch (error) {
    setResultsError(
      error?.message || "Failed to export student results."
    );
  } finally {
    setResultsExporting(false);
  }
};

const resultsPanel = selectedPanel === "results" && selectedCourse ? (
    <div className="lecturer-panel">
      <div className="lecturer-panel-header">
        <div>
          <h2>Manage Results</h2>
          <p>{selectedCourse.course_code || "Course"}  -  {selectedCourse.course_name || "Selected Course"}</p>
        </div>
        <button className="lecturer-action secondary" type="button" onClick={() => setSelectedPanel("students")}>Back Ã‚Â¢-Back Ã‚Â Back</button>
      </div>
      <div
      className="lecturer-results-export"
      style={{
        display: "flex",
        gap: "8px",
        flexWrap: "wrap",
        marginBottom: "16px",
      }}
    >
      <button
        className="lecturer-action secondary"
        type="button"
        disabled={resultsExporting}
        onClick={() => exportResults("csv")}
      >
        {resultsExporting ? "Exporting..." : "Download CSV"}
      </button>

      <button
        className="lecturer-action secondary"
        type="button"
        disabled={resultsExporting}
        onClick={() => exportResults("xlsx")}
      >
        {resultsExporting ? "Exporting..." : "Download Excel"}
      </button>

      <button
        className="lecturer-action secondary"
        type="button"
        disabled={resultsExporting}
        onClick={() => exportResults("pdf")}
      >
        {resultsExporting ? "Exporting..." : "Download PDF"}
      </button>
    </div>

    {resultsLoading && <div className="lecturer-loading">Loading results...</div>}
      {resultsError && <div className="lecturer-error">{resultsError}</div>}
      {!resultsLoading && !resultsError && results && (
        <>
          <div className="lecturer-result-summary">
            <div><strong>{results.total_students ?? 0}</strong><span>Students</span></div>
            <div><strong>{results.total_assessments ?? 0}</strong><span>Assessments</span></div>
          </div>
          {(!results.students || results.students.length === 0) ? (
            <div className="lecturer-empty">No students are enrolled in this course.</div>
          ) : (
            <div className="lecturer-results-table-wrap">
              <table className="lecturer-results-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    {(results.students[0]?.assessments || []).map((assessment) => (
                      <th key={assessment.assessment_id}>
                        {assessment.title}<small> / {assessment.max_score}</small>
                      </th>
                    ))}
                    <th>Total</th>
                    <th>Percentage</th>
                    <th>Grade</th>
                  </tr>
                </thead>
                <tbody>
                  {results.students.map((student) => {
                    const assessments = student.assessments || [];
                    const totalMax = assessments.reduce((sum, a) => sum + Number(a.max_score || 0), 0);
                    const totalScore = assessments.reduce((sum, a) => sum + (a.score != null && !a.is_absent ? Number(a.score) : 0), 0);
                    const marked = assessments.filter((a) => a.score != null || a.is_absent).length;
                    const percentage = totalMax > 0 ? (totalScore / totalMax) * 100 : 0;
                    const grade = percentage >= 70 ? "A" : percentage >= 60 ? "B" : percentage >= 50 ? "C" : percentage >= 45 ? "D" : percentage >= 40 ? "E" : "F";
                    return (
                      <tr key={student.student_id}>
                        <td>
                          <strong>{student.first_name || ""} {student.last_name || ""}</strong>
                          <small>{student.matric_number || student.registration_number || student.student_id}</small>
                        </td>
                        {assessments.map((assessment) => (
                          <td key={assessment.assessment_id}>
                            <div className="lecturer-score-cell">
                              <input type="number" min="0" max={assessment.max_score} step="0.01" value={assessment.score ?? ""} placeholder={assessment.is_absent ? "Absent" : "Score"} onBlur={(event) => saveScore({ student_id: student.student_id, assessment_id: assessment.assessment_id, score: event.target.value, is_absent: false })} />
                              {assessment.is_absent ? (
                                <small>Absent</small>
                              ) : assessment.score == null ? (
                                <small>Missing</small>
                              ) : (
                                <small>{assessment.percentage}%</small>
                              )}
                            </div>
                          </td>
                        ))}
                        <td><strong>{totalScore.toFixed(2)} / {totalMax.toFixed(2)}</strong><small>{marked}/{assessments.length} marked</small></td>
                        <td>{percentage.toFixed(2)}%</td>
                        <td><strong>{marked === 0 ? "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â" : grade}</strong></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  ) : null;

  const assessmentPanel = selectedPanel === "assessments" && selectedCourse ? (
    <section className="lecturer-card">
      <div className="lecturer-section-header">
        <div>
          <h2>Assessments</h2>
          <p>{selectedCourse.course_code || "Course"}  -  {selectedCourse.course_name || "Selected Course"}</p>
        </div>
        <button className="lecturer-action secondary" type="button" onClick={() => { setSelectedCourse(null); setSelectedPanel("students"); }}>
          Back Ã‚Â¢-Back Ã‚Â Back to Courses
        </button>
      </div>

      <div style={{ marginBottom: 18 }}>
        <button
          className="lecturer-action"
          type="button"
          onClick={() =>
            setShowAssessmentForm(!showAssessmentForm)
          }
        >
          {showAssessmentForm
            ? "Cancel"
            : "+ Create Assessment"}
        </button>
      </div>

      {showAssessmentForm && (
        <div
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 18,
            marginBottom: 20,
            background: "#fafcff",
          }}
        >
          <h3 style={{ marginTop: 0 }}>
            {editingAssessmentId ? "Edit Assessment" : "Create Assessment"}
          </h3>

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(2, minmax(0, 1fr))",
              gap: 12,
            }}
          >
            <input
              placeholder="Assessment title"
              value={assessmentForm.title}
              onChange={(e) =>
                setAssessmentForm({
                  ...assessmentForm,
                  title: e.target.value,
                })
              }
            />

            <select
              value={assessmentForm.assessment_type}
              onChange={(e) =>
                setAssessmentForm({
                  ...assessmentForm,
                  assessment_type: e.target.value,
                })
              }
            >
              <option value="ca">CA</option>
              <option value="test">Test</option>
              <option value="assignment">
                Assignment
              </option>
              <option value="exam">Exam</option>
              <option value="practical">
                Practical
              </option>
              <option value="project">Project</option>
              <option value="quiz">Quiz</option>
              <option value="other">Other</option>
            </select>

            <select
              value={assessmentForm.max_score}
              onChange={(e) =>
                setAssessmentForm({
                  ...assessmentForm,
                  max_score: Number(e.target.value),
                })
              }
            >
              <option value={30}>30 marks</option>
              <option value={40}>40 marks</option>
              <option value={50}>50 marks</option>
              <option value={60}>60 marks</option>
              <option value={70}>70 marks</option>
              <option value={80}>80 marks</option>
              <option value={90}>90 marks</option>
              <option value={100}>100 marks</option>
            </select>            <input
              type="date"
              value={assessmentForm.assessment_date}
              onChange={(e) =>
                setAssessmentForm({
                  ...assessmentForm,
                  assessment_date: e.target.value,
                })
              }
            />

            
            <input
              type="number"
              min="0"
              max="100"
              placeholder="Weight (%)"
              value={assessmentForm.weight}
              onChange={(e) =>
                setAssessmentForm({
                  ...assessmentForm,
                  weight: e.target.value,
                })
              }
            />

            <textarea
              placeholder="Description (optional)"
              value={assessmentForm.description}
              onChange={(e) =>
                setAssessmentForm({
                  ...assessmentForm,
                  description: e.target.value,
                })
              }
              style={{
                gridColumn: "1 / -1",
                minHeight: 80,
              }}
            />
          </div>

          <button
            className="lecturer-action"
            type="button"
            disabled={assessmentSaving}
            onClick={saveAssessment}
            style={{ marginTop: 12 }}
          >
            {assessmentSaving
              ? "Saving..."
              : "Save Assessment"}
          </button>
        </div>
      )}

      {assessmentsLoading && <div className="lecturer-empty">Loading assessments...</div>}
      {assessmentsError && <div className="lecturer-error">{assessmentsError}</div>}

      {!assessmentsLoading && !assessmentsError && assessments.length === 0 && (
        <div className="lecturer-empty">
          <h3>No assessments</h3>
          <p>No assessments have been created for this course yet.</p>
        </div>
      )}

      {!assessmentsLoading && !assessmentsError && assessments.length > 0 && (
        <div className="lecturer-table-wrap">
          <table className="lecturer-table">
            <thead>
              <tr>
                <th>Assessment</th>
                <th>Type</th>
                <th>Total Marks</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((assessment, index) => (
                <tr key={assessment.id || index}>
                  <td>{assessment.title || assessment.name || assessment.assessment_name || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                  <td>{assessment.assessment_type || assessment.type || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                  <td>{assessment.total_marks ?? assessment.max_score ?? "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                  <td>{assessment.status || "active"}</td>
                    <td>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        <button
                          type="button"
                          className="lecturer-action secondary"
                          disabled={assessmentSaving}
                          onClick={() => startEditAssessment(assessment)}
                        >
                          Edit
                        </button>

                        <button
                          type="button"
                          className="lecturer-action secondary"
                          disabled={assessmentSaving}
                          onClick={() => deleteAssessment(assessment)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  ) : null;

  const aiMarkingPanel =
    selectedPanel === "ai-marking" && selectedCourse ? (
      <section className="lecturer-card">
        <div className="lecturer-section-header">
          <div>
            <h2>AI Marking</h2>
            <p>
              {selectedCourse.course_code || "Course"}  -  {selectedCourse.course_name || "Selected Course"}
            </p>
          </div>

          <button
            className="lecturer-action secondary"
            type="button"
            onClick={() => {
              setSelectedCourse(null);
              setSelectedPanel("students");
            }}
          >
            Back Ã‚Â¢-Back Ã‚Â Back to Courses
          </button>
        </div>

        <div
          style={{
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 18,
            marginBottom: 20,
            background: "#fafcff",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Select Assessment</h3>

          {assessmentsLoading ? (
            <div className="lecturer-empty">Loading assessments...</div>
          ) : (
            <select
              value={
                aiMarkingAssessment?.id != null
                  ? String(aiMarkingAssessment.id)
                  : ""
              }

              onChange={(e) => {
  const selectedFiles = Array.from(e.target.files || []);

  if (!selectedFiles.length) return;

  setAIMarkingError("");

  setAIAnswerFiles((previousFiles) => {
    const existingKeys = new Set(
      previousFiles.map(
        (file) => `${file.name}-${file.size}-${file.lastModified}`
      )
    );

    const newFiles = selectedFiles.filter(
      (file) =>
        !existingKeys.has(
          `${file.name}-${file.size}-${file.lastModified}`
        )
    );

    const combinedFiles = [...previousFiles, ...newFiles];

    if (combinedFiles.length > 600) {
      setAIMarkingError(
        "Maximum 600 answer papers per upload batch. Extra files were not added."
      );
      return combinedFiles.slice(0, 600);
    }

    return combinedFiles;
  });

  e.target.value = "";
}}
              style={{
                width: "100%",
                padding: 12,
                borderRadius: 8,
                border: "1px solid #cbd5e1",
              }}
            >
              <option value="">Select an assessment</option>

              {assessments.map((assessment) => (
                <option
                  key={assessment.id}
                  value={String(assessment.id)}
                >
                  {assessment.title ||
                    assessment.name ||
                    assessment.assessment_name ||
                    `Assessment #${assessment.id}`}
                  {" - "}
                  {assessment.max_score ??
                    assessment.total_marks ??
                    0}{" "}
                  marks
                </option>
              ))}
            </select>
          )}
        </div>

        {aiMarkingAssessment && (
          <>
            <div style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 18, marginBottom: 20 }}>
              <h3 style={{ marginTop: 0 }}>1. Upload Question Paper</h3>
              <p style={{ color: "#64748b" }}>
                Upload the lecturer's question paper. PDF, Word, image and text formats are supported by the backend.
              </p>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.webp,.heic,.heif"
                onChange={(e) => setAIQuestionFile(e.target.files?.[0] || null)}
              />
              <button
                className="lecturer-action"
                type="button"
                disabled={aiMarkingUploading || !aiQuestionFile}
                onClick={uploadAIQuestionPaper}
                style={{ marginTop: 12 }}
              >
                {aiMarkingUploading ? "Uploading..." : "Upload Question Paper"}
              </button>
            </div>

            <div style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 18, marginBottom: 20 }}>
            {aiDetectedQuestions.length > 0 && (
              <div
                style={{
                  border: "1px solid #e2e8f0",
                  borderRadius: 12,
                  padding: 18,
                  marginBottom: 20,
                  background: "#f8fafc",
                }}
              >
                <h3 style={{ marginTop: 0 }}>
                  Detected Questions & Marks
                </h3>

                <p style={{ color: "#64748b" }}>
                  Review the questions and maximum marks detected from the
                  uploaded question paper before continuing.
                </p>

                <div style={{ overflowX: "auto" }}>
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                    }}
                  >
                    <thead>
                      <tr>
                        <th style={{ textAlign: "left", padding: 10 }}>
                          Question
                        </th>
                        <th style={{ textAlign: "left", padding: 10 }}>
                          Question Text
                        </th>
                        <th style={{ textAlign: "right", padding: 10 }}>
                          Maximum Mark
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {aiDetectedQuestions.map((question) => (
                        <tr key={question.id || question.question_number}>
                          <td style={{ padding: 10, verticalAlign: "top" }}>
                            {question.question_number}
                          </td>

                          <td style={{ padding: 10 }}>
                            {question.question_text || "Back Ã‚Â¢Back Ã‚Â¬Back Ã‚Â"}
                          </td>

                          <td style={{ padding: 10, textAlign: "right" }}>
                            <input
                              type="number"
                              min="0.5"
                              step="0.5"
                              value={
                                aiQuestionMarks[
                                  question.id || question.question_number
                                ] ?? ""
                              }
                              onChange={(e) =>
                                setAIQuestionMarks((previous) => ({
                                  ...previous,
                                  [question.id || question.question_number]:
                                    e.target.value,
                                }))
                              }
                              style={{
                                width: 90,
                                padding: 8,
                                border: "1px solid #cbd5e1",
                                borderRadius: 6,
                              }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div
                  style={{
                    marginTop: 14,
                    paddingTop: 12,
                    borderTop: "1px solid #e2e8f0",
                    fontWeight: 600,
                  }}
                >
                  Total detected marks:{" "}
                  {aiDetectedQuestions.reduce(
                    (total, question) =>
                      total + Number(question.max_score || 0),
                    0
                  )}
                </div>
              </div>
            )}
              <h3 style={{ marginTop: 0 }}>2. Upload Student Answer Papers</h3>
              <p style={{ color: "#64748b" }}>
                Select one or many student answer papers. Students can be matched automatically when their identity is detected.
              </p>
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.webp,.heic,.heif"
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  if (files.length > 600) {
                    setAIMarkingError("You can select a maximum of 600 answer papers per upload batch.");
                    setAIAnswerFiles(files.slice(0, 600));
                    return;
                  }
                  setAIMarkingError("");
                  setAIAnswerFiles(files);
                }}
              />
              {aiAnswerFiles.length > 0 && (
                <div style={{ marginTop: 10, color: "#475569", fontSize: 14 }}>
                  <strong>{aiAnswerFiles.length}</strong> answer paper(s) selected.
                  {aiAnswerFiles.length >= 600 && " Maximum batch reached."}
                </div>
              )}
              <div style={{ marginTop: 10, padding: 10, borderRadius: 8, background: "#f1f5f9", color: "#475569", fontSize: 13 }}>
                Large batches are supported. For university-scale marking, upload in batches of up to 600 papers and process them as AI marking jobs.
              </div>
              <button
                className="lecturer-action"
                type="button"
                disabled={aiMarkingUploading || !aiAnswerFiles.length}
                onClick={uploadAIAnswerPapers}
                style={{ marginTop: 12 }}
              >
                {aiMarkingUploading ? "Uploading..." : "Upload Answer Papers"}
              </button>
            </div>

            <div style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 18, marginBottom: 20, background: "#fafcff" }}>
              <h3 style={{ marginTop: 0 }}>3. Run AI Marking</h3>
              <p style={{ color: "#64748b" }}>
                AI will evaluate submitted answers against the uploaded questions. Suggested marks remain subject to lecturer review. Student identity and attendance eligibility must be verified before final results are accepted.
              </p>
              <div style={{ marginBottom: 12, padding: 10, borderRadius: 8, background: "#fff7ed", color: "#9a3412", fontSize: 13 }}>
                <strong>Academic integrity:</strong> papers that cannot be matched to an enrolled student or verified attendance record should be held for manual review rather than automatically accepted.
              </div>
              <button
                className="lecturer-action"
                type="button"
                disabled={aiMarkingLoading}
                onClick={startAIMarking}
              >
                {aiMarkingLoading ? "Running AI Marking..." : "Run AI Marking"}
              </button>
              {aiMarkingJobId && (
                <button
                  className="lecturer-action secondary"
                  type="button"
                  disabled={aiMarkingLoading}
                  onClick={() => loadAIMarkingResults(aiMarkingJobId)}
                  style={{ marginLeft: 10 }}
                >
                  Refresh Results
                </button>
              )}
            </div>

            {aiMarkingError && <div className="lecturer-error">{aiMarkingError}</div>}

            {aiMarkingMessage && (
              <div style={{ padding: 12, borderRadius: 8, background: "#ecfdf5", color: "#166534", marginBottom: 18 }}>
                {aiMarkingMessage}
              </div>
            )}

            {aiPendingSubmissions.length > 0 && (
              <div
                style={{
                  marginBottom: 18,
                  padding: 16,
                  border: "1px solid #f59e0b",
                  borderRadius: 10,
                  background: "#fffbeb",
                }}
              >
                <h3 style={{ marginTop: 0 }}>
                  Papers Awaiting Student Identification
                </h3>

                <p style={{ marginTop: 0 }}>
                  AI marking processed these papers, but could not identify
                  the student. Select the correct enrolled student.
                </p>

                {aiPendingSubmissions.map((submission) => (
                  <div
                    key={submission.submission_id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      marginBottom: 10,
                      padding: 10,
                      background: "#fff",
                      borderRadius: 8,
                      border: "1px solid #fde68a",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <strong>
                        {submission.file_name || "Answer paper"}
                      </strong>

                      <div style={{ fontSize: 12, color: "#92400e" }}>
                        Submission #{submission.submission_id}
                      </div>
                    </div>

                    <select
                      value={
                        aiMatchingStudentIds[submission.submission_id] || ""
                      }
                      onChange={(e) =>
                        setAIMatchingStudentIds((previous) => ({
                          ...previous,
                          [submission.submission_id]: e.target.value,
                        }))
                      }
                    >
                      <option value="">
                        Select enrolled student
                      </option>

                      {students.map((student) => {
                        const studentId =
                          student.student_id ?? student.id;

                        const studentName =
                          student.name ||
                          [
                            student.first_name,
                            student.middle_name,
                            student.last_name,
                          ]
                            .filter(Boolean)
                            .join(" ");

                        const identifier =
                          student.matric_number ||
                          student.registration_number ||
                          student.student_number ||
                          "";

                        return (
                          <option key={studentId} value={studentId}>
                            {studentName || "Student"}{" "}
                            {identifier ? `(${identifier})` : ""}
                          </option>
                        );
                      })}
                    </select>

                    <button
                      className="lecturer-action primary"
                      type="button"
                      disabled={
                        aiMatchingId === submission.submission_id ||
                        !aiMatchingStudentIds[submission.submission_id]
                      }
                      onClick={() =>
                        matchAIStudent({
                          submission_id: submission.submission_id,
                        })
                      }
                    >
                      {aiMatchingId === submission.submission_id
                        ? "Matching..."
                        : "Match Student"}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {aiMarkingResults.length > 0 && (
              <div>
                <h3>AI Marking Results</h3>
                <div className="lecturer-table-wrap">
                  <table className="lecturer-table">
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>Question</th>
                        <th>AI Mark</th>
                        <th>Max</th>
                        <th>Confidence</th>
                        <th>Integrity / Status</th>
                        <th>Evidence / Feedback</th>
                        <th>Lecturer Mark</th>
                        <th>Review</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aiMarkingResults.map((result) => (
                        <tr key={result.id}>
                          <td>
                            {result.student_name ||
                            result.matric_number ||
                            result.student_id ? (
                              result.student_name ||
                              result.matric_number ||
                              result.student_id
                            ) : (
                              <div style={{ minWidth: 220 }}>
                                <div
                                  style={{
                                    fontSize: 12,
                                    fontWeight: 700,
                                    color: "#991b1b",
                                    marginBottom: 6,
                                  }}
                                >
                                  Student not identified
                                </div>

                                <select
                                  value={
                                    aiMatchingStudentIds[
                                      result.submission_id
                                    ] || ""
                                  }
                                  onChange={(e) =>
                                    setAIMatchingStudentIds((previous) => ({
                                      ...previous,
                                      [result.submission_id]: e.target.value,
                                    }))
                                  }
                                  style={{
                                    width: "100%",
                                    padding: 7,
                                    borderRadius: 6,
                                    border: "1px solid #cbd5e1",
                                  }}
                                  disabled={
                                    aiMatchingId === result.submission_id
                                  }
                                >
                                  <option value="">
                                    Select enrolled student
                                  </option>

                                  {students.map((student) => {
                                    const studentId = student.student_id ?? student.id;

                                    const studentName =
                                      student.name ||
                                      [
                                        student.first_name,
                                        student.middle_name,
                                        student.last_name,
                                      ]
                                        .filter(Boolean)
                                        .join(" ");

                                    const identifier =
                                      student.matric_number ||
                                      student.registration_number ||
                                      student.student_number ||
                                      "";

                                    return (
                                      <option
                                        key={studentId}
                                        value={studentId}
                                      >
                                        {studentName || "Student"}{" "}
                                        {identifier
                                          ? `(${identifier})`
                                          : ""}
                                      </option>
                                    );
                                  })}
                                </select>

                                <button
                                  className="lecturer-action"
                                  type="button"
                                  style={{ marginTop: 6 }}
                                  disabled={
                                    aiMatchingId === result.submission_id ||
                                    !aiMatchingStudentIds[
                                      result.submission_id
                                    ]
                                  }
                                  onClick={() => matchAIStudent(result)}
                                >
                                  {aiMatchingId === result.submission_id
                                    ? "Matching..."
                                    : "Match Student"}
                                </button>
                              </div>
                            )}
                          </td>
                          <td>{result.question_number || result.question_id}</td>
                          <td>{result.suggested_score ?? "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                          <td>{result.max_score ?? "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                          <td>
                            {result.confidence !== null && result.confidence !== undefined
                              ? `${Math.round(Number(result.confidence) * 100)}%`
                              : "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}
                          </td>
                          <td>
                            {(() => {
                              const status = String(result.status || "").toLowerCase();
                              const matched =
                                result.student_id ||
                                result.student_name ||
                                result.matric_number;

                              let label = status || "pending_review";
                              let background = "#fef3c7";
                              let color = "#92400e";

                              if (status === "approved" || status === "reviewed") {
                                background = "#dcfce7";
                                color = "#166534";
                              } else if (status === "overridden" || status === "override") {
                                background = "#dbeafe";
                                color = "#1e40af";
                              } else if (
                                status === "manual_review" ||
                                status === "needs_review" ||
                                !matched
                              ) {
                                label = "Manual review";
                                background = "#fee2e2";
                                color = "#991b1b";
                              }

                              return (
                                <div style={{ minWidth: 120 }}>
                                  <span
                                    style={{
                                      display: "inline-block",
                                      padding: "5px 9px",
                                      borderRadius: 999,
                                      background,
                                      color,
                                      fontSize: 12,
                                      fontWeight: 700,
                                    }}
                                  >
                                    {label.replaceAll("_", " ")}
                                  </span>
                                  {!matched && (
                                    <div style={{ marginTop: 6, fontSize: 12, color: "#991b1b" }}>
                                      Student identity not verified
                                    </div>
                                  )}
                                  {result.attendance_verified === false && (
                                    <div style={{ marginTop: 6, fontSize: 12, color: "#991b1b" }}>
                                      Attendance not verified
                                    </div>
                                  )}
                                </div>
                              );
                            })()}
                          </td>
                          <td>
                            <div style={{ maxWidth: 320, whiteSpace: "normal" }}>
                              {result.grading_evidence || result.feedback || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}
                            </div>
                          </td>
                          <td>
                            <input
                              type="number"
                              min="0"
                              max={result.max_score}
                              step="0.5"
                              value={aiReviewScores[result.id] ?? result.suggested_score ?? ""}
                              onChange={(e) => setAIReviewScores({ ...aiReviewScores, [result.id]: e.target.value })}
                              style={{ width: 80, padding: 7 }}
                              disabled={result.status !== "pending_review"}
                            />
                          </td>
                          <td>
                            {result.status === "pending_review" ? (
                              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                <input
                                  type="text"
                                  placeholder="Lecturer comment"
                                  value={aiReviewComments[result.id] || ""}
                                  onChange={(e) => setAIReviewComments({ ...aiReviewComments, [result.id]: e.target.value })}
                                />
                                <div style={{ display: "flex", gap: 6 }}>
                                  <button
                                    className="lecturer-action"
                                    type="button"
                                    disabled={aiReviewingId === result.id}
                                    onClick={() => reviewAIResult(result, true)}
                                  >
                                    Approve
                                  </button>
                                  <button
                                    className="lecturer-action secondary"
                                    type="button"
                                    disabled={aiReviewingId === result.id}
                                    onClick={() => reviewAIResult(result, false)}
                                  >
                                    Override
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <span>{result.status || "reviewed"}</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    ) : null;

  if (loading) {
    return (
      <div className="lecturer-page">
        <div className="lecturer-loading">
          Loading lecturer dashboard...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="lecturer-page">
        <button
          onClick={onBack}
          className="lecturer-back"
          type="button"
        >
          Back Ã‚Â¢-Back Ã‚Â Back
        </button>

        <div className="lecturer-error">
          {error}
        </div>
      </div>
    );
  }

  const lecturer = data?.lecturer || {};
  const summary = data?.summary || {};
  const courses = data?.courses || [];

  const fullName = [
    lecturer.title,
    lecturer.first_name,
    lecturer.middle_name,
    lecturer.last_name,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="lecturer-page">
      <style>{`
        .lecturer-page {
          min-height: 100vh;
          padding: 28px;
          background: linear-gradient(
            180deg,
            #f8fafc 0%,
            #eef2f7 100%
          );
          color: #172033;
          box-sizing: border-box;
        }

        .lecturer-container {
          max-width: 1400px;
          margin: 0 auto;
        }

        .lecturer-back {
          border: 1px solid #d8dee9;
          background: white;
          color: #172033;
          border-radius: 10px;
          padding: 10px 14px;
          cursor: pointer;
          font-weight: 600;
          margin-bottom: 18px;
        }

        .lecturer-header {
          margin-bottom: 24px;
        }

        .lecturer-title {
          margin: 0;
          font-size: 30px;
        }

        .lecturer-subtitle {
          margin: 7px 0 0;
          color: #64748b;
          font-size: 14px;
        }

        .lecturer-profile {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          padding: 22px;
          margin-bottom: 20px;
          box-shadow: 0 8px 30px rgba(15,23,42,.05);
        }

        .lecturer-name {
          font-size: 22px;
          font-weight: 800;
        }

        .lecturer-meta {
          margin-top: 7px;
          color: #64748b;
          font-size: 14px;
        }

        .lecturer-metrics {
          display: grid;
          grid-template-columns: repeat(
            3,
            minmax(0, 1fr)
          );
          gap: 14px;
          margin-bottom: 20px;
        }

        .lecturer-metric {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 14px;
          padding: 20px;
        }

        .lecturer-metric-label {
          color: #64748b;
          font-size: 13px;
          font-weight: 600;
        }

        .lecturer-metric-value {
          margin-top: 8px;
          font-size: 30px;
          font-weight: 800;
        }

        .lecturer-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          padding: 22px;
          box-shadow: 0 8px 30px rgba(15,23,42,.05);
        }

        .lecturer-section-title {
          margin: 0 0 16px;
          font-size: 20px;
        }

        .lecturer-course {
          border: 1px solid #e2e8f0;
          border-radius: 13px;
          padding: 18px;
          margin-bottom: 12px;
          background: #fafcff;
        }

        .lecturer-course:last-child {
          margin-bottom: 0;
        }

        .lecturer-course-title {
          font-size: 17px;
          font-weight: 750;
        }

        .lecturer-course-meta {
          margin-top: 7px;
          color: #64748b;
          font-size: 13px;
        }

        .lecturer-permissions {
          display: flex;
          flex-wrap: wrap;
          gap: 7px;
          margin-top: 12px;
        }

        .lecturer-permission {
          background: #dcfce7;
          color: #166534;
          border-radius: 999px;
          padding: 5px 9px;
          font-size: 11px;
          font-weight: 700;
        }

        .lecturer-empty,
        .lecturer-loading,
        .lecturer-error {
          max-width: 900px;
          margin: 80px auto;
          text-align: center;
          padding: 30px;
          background: white;
          border-radius: 16px;
          border: 1px solid #e2e8f0;
        }

        .lecturer-error {
          color: #991b1b;
          background: #fee2e2;
        }

        @media (max-width: 700px) {
          .lecturer-page {
            padding: 15px;
          }

          .lecturer-metrics {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div className="lecturer-container">
        <button
          onClick={onBack}
          className="lecturer-back"
          type="button"
        >
          Back Ã‚Â¢-Back Ã‚Â Back
        </button>

        <header className="lecturer-header">
          <h1 className="lecturer-title">
            Lecturer Dashboard
          </h1>

          <p className="lecturer-subtitle">
            University AI academic management
          </p>
        </header>

        <section className="lecturer-profile">
          <div className="lecturer-name">
            {fullName || "Lecturer"}
          </div>

          <div className="lecturer-meta">
            Staff ID: {lecturer.staff_id || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}  -  Status:{" "}
            {lecturer.status || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}
          </div>
        </section>

        <section className="lecturer-metrics">
          <div className="lecturer-metric">
            <div className="lecturer-metric-label">
              Courses
            </div>

            <div className="lecturer-metric-value">
              {summary.total_courses ?? 0}
            </div>
          </div>

          <div className="lecturer-metric">
            <div className="lecturer-metric-label">
              Students
            </div>

            <div className="lecturer-metric-value">
              {summary.total_students ?? 0}
            </div>
          </div>

          <div className="lecturer-metric">
            <div className="lecturer-metric-label">
              Assessments
            </div>

            <div className="lecturer-metric-value">
              {summary.total_assessments ?? 0}
            </div>
          </div>
        </section>

        {assessmentPanel}

      {attendancePanel}
      {resultsPanel}
      {courseDocumentsPanel}
      {aiMarkingPanel}

      {selectedPanel === "students" && selectedCourse ? (
        <section className="lecturer-card">
          <div className="lecturer-section-header">
            <div>
              <h2>Students</h2>
              <p>{selectedCourse.course_code || "Course"}  -  {selectedCourse.course_name || "Selected Course"}</p>
            </div>
            <button className="lecturer-action secondary" type="button" onClick={() => setSelectedCourse(null)}>
              Back Ã‚Â¢-Back Ã‚Â Back to Courses
            </button>
          </div>

          <div style={{ marginBottom: 18 }}>
            <button className="lecturer-action" type="button" onClick={() => setShowAddStudentForm(!showAddStudentForm)}>
              {showAddStudentForm ? "Cancel" : "+ Add Student"}
            </button>
          </div>

          <div
      style={{
        display: "flex",
        gap: 10,
        flexWrap: "wrap",
        alignItems: "center",
        marginBottom: 16,
      }}
    >
      <input
        type="text"
        value={studentSearch}
        onChange={(e) => setStudentSearch(e.target.value)}
        placeholder="Search by student name or ID"
        style={{ flex: "1 1 260px" }}
      />

      <select
        value={studentStatusFilter}
        onChange={(e) => setStudentStatusFilter(e.target.value)}
      >
        <option value="all">All statuses</option>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
      </select>
    </div>

    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 10,
        padding: 14,
        marginBottom: 18,
      }}
    >
      <strong>Import Students</strong>

      <div
        style={{
          display: "flex",
          gap: 10,
          flexWrap: "wrap",
          alignItems: "center",
          marginTop: 10,
        }}
      >
        <input
          id="lecturer-student-import-file"
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={(e) => {
            setStudentImportFile(e.target.files?.[0] || null);
            setStudentImportPreview(null);
            setStudentImportError("");
            setStudentImportMessage("");
          }}
        />

        <button
          type="button"
          disabled={!studentImportFile || studentImportLoading}
          onClick={previewStudentImportFile}
        >
          {studentImportLoading ? "Previewing..." : "Preview Import"}
        </button>

        {studentImportPreview && (
          <button
            type="button"
            disabled={studentImportCommitting}
            onClick={commitStudentImport}
          >
            {studentImportCommitting ? "Importing..." : "Import Students"}
          </button>
        )}

        {studentImportFile && (
          <button
            type="button"
            onClick={() => {
              setStudentImportFile(null);
              setStudentImportPreview(null);
              setStudentImportError("");
              setStudentImportMessage("");

              const input = document.getElementById(
                "lecturer-student-import-file"
              );

              if (input) input.value = "";
            }}
          >
            Clear
          </button>
        )}
      </div>

      {studentImportError && (
        <div style={{ marginTop: 10 }}>
          {studentImportError}
        </div>
      )}

      {studentImportMessage && (
        <div style={{ marginTop: 10 }}>
          {studentImportMessage}
        </div>
      )}

      {studentImportPreview && (
        <div style={{ marginTop: 14 }}>
          <strong>Import Preview</strong>

          <pre
            style={{
              whiteSpace: "pre-wrap",
              overflowX: "auto",
              marginTop: 8,
            }}
          >
            {JSON.stringify(studentImportPreview, null, 2)}
          </pre>
        </div>
      )}
    </div>

    {showAddStudentForm && (
            <div className="lecturer-card" style={{ marginBottom: 18 }}>
              <h3>Add Student</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
                <input placeholder="Matric Number *" value={studentForm.matric_number} onChange={(e) => setStudentForm({ ...studentForm, matric_number: e.target.value })} />
                <input placeholder="First Name *" value={studentForm.first_name} onChange={(e) => setStudentForm({ ...studentForm, first_name: e.target.value })} />
                <input placeholder="Middle Name" value={studentForm.middle_name} onChange={(e) => setStudentForm({ ...studentForm, middle_name: e.target.value })} />
                <input placeholder="Last Name *" value={studentForm.last_name} onChange={(e) => setStudentForm({ ...studentForm, last_name: e.target.value })} />
                <input placeholder="Level" value={studentForm.level} onChange={(e) => setStudentForm({ ...studentForm, level: e.target.value })} />
                <input type="number" placeholder="Entry Year" value={studentForm.entry_year} onChange={(e) => setStudentForm({ ...studentForm, entry_year: e.target.value })} />
                <input type="number" placeholder="Graduation Year" value={studentForm.graduation_year} onChange={(e) => setStudentForm({ ...studentForm, graduation_year: e.target.value })} />
                <input placeholder="Phone" value={studentForm.phone} onChange={(e) => setStudentForm({ ...studentForm, phone: e.target.value })} />
              </div>
              <div style={{ marginTop: 14 }}>
                <button className="lecturer-action" type="button" onClick={saveStudent} disabled={studentSaving}>
                  {studentSaving ? "Saving..." : "Save Student"}
                </button>
              </div>
            </div>
          )}

          {studentsLoading && <div className="lecturer-empty">Loading students...</div>}

          {studentsError && <div className="lecturer-error">{studentsError}</div>}

          {!studentsLoading && !studentsError && students.length === 0 && (
            <div className="lecturer-empty">
              <h3>No students enrolled</h3>
              <p>No students are currently enrolled in this course.</p>
            </div>
          )}

          {!studentsLoading && !studentsError && students.length > 0 && (
            <div className="lecturer-table-wrap">
              <table className="lecturer-table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Matric Number</th>
                    <th>Level</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((student, index) => (
                    <tr key={student.id || student.student_id || index}>
                      <td>{student.name || [student.first_name, student.last_name].filter(Boolean).join(" ") || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                      <td>{student.matric_number || student.registration_number || student.student_number || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                      <td>{student.level || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}</td>
                      <td>{student.status || "active"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : (
        <section className="lecturer-card">
          <h2 className="lecturer-section-title">
            Assigned Courses
          </h2>

          {courses.length === 0 ? (
            <div className="lecturer-empty">
              No courses have been assigned yet.
            </div>
          ) : (
            courses.map((course) => (
              <div
                className="lecturer-course"
                key={course.lecturer_course_id}
              >
                <div className="lecturer-course-title">
                  Course #{course.course_id}  -  Offering #
                  {course.course_offering_id}
                </div>

                <div className="lecturer-course-meta">
                  Level: {course.level || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}  -  Section:{" "}
                  {course.section || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}  -  Role:{" "}
                  {course.role || "Back Ã‚Â¢-Ã‚Â¡Back Ã‚Â¬-Ã‚Â"}
                </div>

                <div className="lecturer-course-meta">
                  Students: {course.student_count ?? 0}  - 
                  Assessments:{" "}
                  {course.assessment_count ?? 0}
                </div>

                <div className="lecturer-actions">
                  {course.can_manage_students && (
                    <button className="lecturer-action" type="button" onClick={() => openStudents(course)}>
                      Manage Students
                    </button>
                  )}

                  {course.can_manage_students && (
                    <button className="lecturer-action secondary" type="button" onClick={() => openAttendance(course)}>
                      Manage Attendance
                    </button>
                  )}
                  {course.can_manage_assessments && (
                    <button
                      className="lecturer-action secondary"
                      type="button"
                      onClick={() => openAssessments(course)}
                    >
                      Manage Assessments
                    </button>
                  )}
                  {course.can_manage_results && (
                    <button className="lecturer-action secondary" type="button" onClick={() => openResults(course)}>
                      Manage Results
                    </button>
                  )}
                  {(course.can_manage_results || course.can_manage_assessments || course.can_manage_students) && (
                    <button
                      className="lecturer-action secondary"
                      type="button"
                      onClick={() => openAIMarking(course)}
                    >
                      AI Marking
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </section>
      )}
      </div>
    </div>
  );
}









































