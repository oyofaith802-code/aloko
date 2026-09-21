import { useEffect, useMemo, useState } from "react";
import { apiFetch, askStudentCourseAI } from "./api";

function formatDate(value) {
  if (!value) return "â€”";

  try {
    return new Date(value).toLocaleDateString();
  } catch {
    return String(value);
  }
}

function formatStatus(value) {
  if (!value) return "â€”";

  return String(value)
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function StatusBadge({ status }) {
  const value = String(status || "").toLowerCase();

  let className = "student-status-neutral";

  if (
    value.includes("active") ||
    value.includes("completed") ||
    value.includes("approved") ||
    value.includes("paid") ||
    value.includes("present") ||
    value.includes("success")
  ) {
    className = "student-status-success";
  } else if (
    value.includes("failed") ||
    value.includes("rejected") ||
    value.includes("absent") ||
    value.includes("error")
  ) {
    className = "student-status-danger";
  } else if (
    value.includes("pending") ||
    value.includes("processing") ||
    value.includes("late")
  ) {
    className = "student-status-warning";
  }

  return (
    <span className={`student-status ${className}`}>
      {formatStatus(status)}
    </span>
  );
}

function EmptyState({ message }) {
  return (
    <div className="student-empty">
      {message}
    </div>
  );
}

export default function StudentDashboard({ onBack }) {
  const [dashboard, setDashboard] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [courseAIQuestion, setCourseAIQuestion] = useState("");
  const [courseAIAnswer, setCourseAIAnswer] = useState("");
  const [courseAISources, setCourseAISources] = useState([]);
  const [courseAIError, setCourseAIError] = useState("");
  const [courseAILoading, setCourseAILoading] = useState(false);
  const [courseAISelected, setCourseAISelected] = useState(null);

  const handleAskCourseAI = async (event) => {
    event.preventDefault();

    if (!courseAISelected) {
      setCourseAIError("Select a course first.");
      return;
    }

    if (!courseAIQuestion.trim()) {
      setCourseAIError("Enter a question.");
      return;
    }

    setCourseAILoading(true);
    setCourseAIError("");
    setCourseAIAnswer("");
    setCourseAISources([]);

    try {
      const result = await askStudentCourseAI(
        courseAISelected.course_offering_id,
        courseAIQuestion.trim()
      );

      setCourseAIAnswer(result?.answer || "No answer was returned.");
      setCourseAISources(result?.sources || []);
    } catch (err) {
      setCourseAIError(
        err?.message ||
          "Unable to answer the course question."
      );
    } finally {
      setCourseAILoading(false);
    }
  };
  const loadDashboard = async (silent = false) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError("");

    try {
      const data = await apiFetch(
        "/university/student/dashboard"
      );

      setDashboard(data);
    } catch (err) {
      setError(
        err?.message ||
          "Unable to load student dashboard."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const student = dashboard?.student || {};

  const courses = dashboard?.courses || [];
  const results = dashboard?.results || [];
  const attendance = dashboard?.attendance || [];
  const clearances = dashboard?.clearances || [];

  const payments = dashboard?.payments || {};
  const invoices = payments.invoices || [];
  const transactions = payments.transactions || [];

  const attendancePercentage = useMemo(() => {
    if (!attendance.length) return null;

    const present = attendance.filter((record) => {
      const status = String(record.status || "").toLowerCase();

      return (
        status === "present" ||
        status === "late" ||
        status === "excused"
      );
    }).length;

    return Math.round(
      (present / attendance.length) * 100
    );
  }, [attendance]);

  if (loading) {
    return (
      <div className="student-page">
        <div className="student-loading">
          Loading student dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="student-page">
      <style>{`
        .student-page {
          min-height: 100vh;
          padding: 28px;
          box-sizing: border-box;
          background:
            radial-gradient(
              circle at top right,
              rgba(59,130,246,.10),
              transparent 32%
            ),
            linear-gradient(
              180deg,
              #f8fafc 0%,
              #eef2f7 100%
            );
          color: #172033;
        }

        .student-container {
          max-width: 1400px;
          margin: 0 auto;
        }

        .student-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 20px;
          margin-bottom: 22px;
        }

        .student-header-left {
          display: flex;
          gap: 14px;
          align-items: flex-start;
        }

        .student-back,
        .student-refresh {
          border: 1px solid #d8dee9;
          background: white;
          color: #172033;
          border-radius: 10px;
          padding: 10px 14px;
          cursor: pointer;
          font-weight: 650;
        }

        .student-back:hover,
        .student-refresh:hover {
          background: #f1f5f9;
        }

        .student-title {
          margin: 0;
          font-size: 30px;
          letter-spacing: -.7px;
        }

        .student-subtitle {
          margin: 6px 0 0;
          color: #64748b;
          font-size: 14px;
        }

        .student-profile {
          padding: 22px;
          margin-bottom: 18px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          box-shadow: 0 8px 30px rgba(15,23,42,.05);
        }

        .student-profile-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
        }

        .student-name {
          font-size: 22px;
          font-weight: 800;
        }

        .student-matric {
          margin-top: 5px;
          color: #64748b;
          font-size: 13px;
        }

        .student-profile-meta {
          display: flex;
          gap: 9px;
          flex-wrap: wrap;
        }

        .student-status {
          display: inline-flex;
          align-items: center;
          padding: 5px 10px;
          border-radius: 999px;
          font-size: 12px;
          font-weight: 700;
          white-space: nowrap;
        }

        .student-status-success {
          background: #dcfce7;
          color: #166534;
        }

        .student-status-danger {
          background: #fee2e2;
          color: #991b1b;
        }

        .student-status-warning {
          background: #fef3c7;
          color: #92400e;
        }

        .student-status-neutral {
          background: #e2e8f0;
          color: #475569;
        }

        .student-metrics {
          display: grid;
          grid-template-columns:
            repeat(4, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 20px;
        }

        .student-metric {
          padding: 18px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 14px;
        }

        .student-metric-label {
          color: #64748b;
          font-size: 13px;
          font-weight: 650;
        }

        .student-metric-value {
          margin-top: 7px;
          font-size: 28px;
          font-weight: 800;
        }

        .student-metric-note {
          margin-top: 3px;
          color: #94a3b8;
          font-size: 12px;
        }

        .student-tabs {
          display: flex;
          gap: 4px;
          padding: 5px;
          margin-bottom: 18px;
          overflow-x: auto;
          background: #e8edf4;
          border-radius: 13px;
        }

        .student-tab {
          border: 0;
          background: transparent;
          color: #64748b;
          border-radius: 9px;
          padding: 10px 15px;
          cursor: pointer;
          font-weight: 650;
          white-space: nowrap;
        }

        .student-tab.active {
          background: white;
          color: #172033;
          box-shadow:
            0 2px 8px rgba(15,23,42,.08);
        }

        .student-card {
          padding: 22px;
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          box-shadow: 0 8px 30px rgba(15,23,42,.05);
        }

        .student-section-title {
          margin: 0;
          font-size: 19px;
        }

        .student-section-description {
          margin: 5px 0 18px;
          color: #64748b;
          font-size: 13px;
        }

        .student-table-wrapper {
          overflow-x: auto;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
        }

        .student-table {
          width: 100%;
          min-width: 680px;
          border-collapse: collapse;
        }

        .student-table th {
          padding: 12px 14px;
          text-align: left;
          background: #f8fafc;
          color: #64748b;
          border-bottom: 1px solid #e2e8f0;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: .35px;
        }

        .student-table td {
          padding: 13px 14px;
          border-bottom: 1px solid #edf2f7;
          font-size: 13px;
        }

        .student-table tr:last-child td {
          border-bottom: 0;
        }

        .student-empty {
          padding: 50px 20px;
          text-align: center;
          color: #64748b;
          background: #f8fafc;
          border-radius: 12px;
        }

        .student-alert {
          margin-bottom: 18px;
          padding: 13px 15px;
          border-radius: 11px;
          background: #fee2e2;
          border: 1px solid #fecaca;
          color: #991b1b;
          font-size: 13px;
          font-weight: 600;
        }

        .student-loading {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          font-size: 15px;
        }

        .student-info-grid {
          display: grid;
          grid-template-columns:
            repeat(2, minmax(0, 1fr));
          gap: 14px;
        }

        .student-info {
          padding: 15px;
          background: #fafcff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
        }

        .student-info-label {
          color: #64748b;
          font-size: 12px;
          margin-bottom: 5px;
        }

        .student-info-value {
          font-weight: 650;
          font-size: 14px;
        }

        @media (max-width: 900px) {
          .student-metrics {
            grid-template-columns:
              repeat(2, minmax(0, 1fr));
          }

          .student-header,
          .student-profile-top {
            flex-direction: column;
            align-items: stretch;
          }
        }

        @media (max-width: 600px) {
          .student-page {
            padding: 15px;
          }

          .student-metrics,
          .student-info-grid {
            grid-template-columns: 1fr;
          }

          .student-title {
            font-size: 24px;
          }
        }
      `}</style>

      <div className="student-container">

        <header className="student-header">
          <div className="student-header-left">
            <button
              className="student-back"
              type="button"
              onClick={onBack}
            >
              â† Back
            </button>

            <div>
              <h1 className="student-title">
                Student Dashboard
              </h1>

              <p className="student-subtitle">
                Academic information, results, attendance,
                clearance and payments.
              </p>
            </div>
          </div>

          <button
            className="student-refresh"
            type="button"
            disabled={refreshing}
            onClick={() => loadDashboard(true)}
          >
            {refreshing ? "Refreshing..." : "â†» Refresh"}
          </button>
        </header>

        {error && (
          <div className="student-alert">
            {error}
          </div>
        )}

        <section className="student-profile">
          <div className="student-profile-top">
            <div>
              <div className="student-name">
                {student.first_name || ""}{" "}
                {student.middle_name || ""}{" "}
                {student.last_name || ""}
              </div>

              <div className="student-matric">
                Matric Number:{" "}
                {student.matric_number || "â€”"}
              </div>
            </div>

            <div className="student-profile-meta">
              <StatusBadge status={student.status} />

              <span className="student-status student-status-neutral">
                Level {student.level || "â€”"}
              </span>
            </div>
          </div>
        </section>

        <section className="student-metrics">

          <div className="student-metric">
            <div className="student-metric-label">
              Courses
            </div>

            <div className="student-metric-value">
              {courses.length}
            </div>

            <div className="student-metric-note">
              Enrolled courses
            </div>
          </div>

          <div className="student-metric">
            <div className="student-metric-label">
              Results
            </div>

            <div className="student-metric-value">
              {results.length}
            </div>

            <div className="student-metric-note">
              Published result records
            </div>
          </div>

          <div className="student-metric">
            <div className="student-metric-label">
              Attendance
            </div>

            <div className="student-metric-value">
              {attendancePercentage === null
                ? "â€”"
                : `${attendancePercentage}%`}
            </div>

            <div className="student-metric-note">
              Attendance rate
            </div>
          </div>

          <div className="student-metric">
            <div className="student-metric-label">
              Payments
            </div>

            <div className="student-metric-value">
              {invoices.length}
            </div>

            <div className="student-metric-note">
              Invoices
            </div>
          </div>

        </section>

        <nav className="student-tabs">
          {[
            ["overview", "Overview"],
            ["courses", "Courses"],
            ["results", "Results"],
            ["attendance", "Attendance"],
            ["clearance", "Clearance"],
            ["payments", "Payments"],
          ].map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={`student-tab ${
                activeTab === id ? "active" : ""
              }`}
              onClick={() => setActiveTab(id)}
            >
              {label}
            </button>
          ))}
        </nav>

        <section className="student-card">

          {activeTab === "overview" && (
            <>
              <h2 className="student-section-title">
                Student Overview
              </h2>

              <p className="student-section-description">
                Your current academic information.
              </p>

              <div className="student-info-grid">
                <div className="student-info">
                  <div className="student-info-label">
                    Student ID
                  </div>
                  <div className="student-info-value">
                    {student.id || "â€”"}
                  </div>
                </div>

                <div className="student-info">
                  <div className="student-info-label">
                    Matric Number
                  </div>
                  <div className="student-info-value">
                    {student.matric_number || "â€”"}
                  </div>
                </div>

                <div className="student-info">
                  <div className="student-info-label">
                    Level
                  </div>
                  <div className="student-info-value">
                    {student.level || "â€”"}
                  </div>
                </div>

                <div className="student-info">
                  <div className="student-info-label">
                    Account Status
                  </div>
                  <div className="student-info-value">
                    <StatusBadge
                      status={student.status}
                    />
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === "courses" && (
            <>
              <h2 className="student-section-title">
                My Courses
              </h2>

              <p className="student-section-description">
                Courses currently assigned to you.
              </p>

              {courses.length === 0 ? (
                <EmptyState message="No enrolled courses found." />
              ) : (
                <div className="student-table-wrapper">
                  <table className="student-table">
                    <thead>
                      <tr>
                        <th>Enrollment</th>
                        <th>Course</th>
                        <th>Offering</th>
                        <th>Session</th>
                        <th>Semester</th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {courses.map((course, index) => (
                        <tr
                          key={
                            course.enrollment_id ??
                            index
                          }
                        >
                          <td>
                            {course.enrollment_id ??
                              "â€”"}
                          </td>

                          <td>
                            {course.course_id ??
                              "â€”"}
                          </td>

                          <td>
                            {course.course_offering_id ??
                              "â€”"}
                          </td>

                          <td>
                            {course.session_id ??
                              "â€”"}
                          </td>

                          <td>
                            {course.semester_id ??
                              "â€”"}
                          </td>

                          <td>
                            <StatusBadge
                              status={course.status}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

              <div className="student-card" style={{ marginTop: 24 }}>
                <h3 className="student-section-title">Course AI</h3>

                <p className="student-section-description">
                  Ask questions about your enrolled course materials.
                </p>

                <div style={{ marginBottom: 16 }}>
                  <label>Select Course</label>

                  <select
                    value={courseAISelected?.course_offering_id ?? ""}
                    onChange={(event) => {
                      const selected = courses.find(
                        (course) =>
                          String(course.course_offering_id) ===
                          event.target.value
                      );

                      setCourseAISelected(selected || null);
                      setCourseAIQuestion("");
                      setCourseAIAnswer("");
                      setCourseAISources([]);
                      setCourseAIError("");
                    }}
                    style={{
                      width: "100%",
                      padding: 10,
                      marginTop: 6,
                    }}
                  >
                    <option value="">Select a course</option>

                    {courses.map((course, index) => (
                      <option
                        key={
                          course.enrollment_id ??
                          course.course_offering_id ??
                          index
                        }
                        value={course.course_offering_id}
                      >
                        {course.course_code ||
                          `Course ${course.course_id}`}{" "}
                        — Offering {course.course_offering_id}
                      </option>
                    ))}
                  </select>
                </div>

                <form onSubmit={handleAskCourseAI}>
                  <textarea
                    value={courseAIQuestion}
                    onChange={(event) =>
                      setCourseAIQuestion(event.target.value)
                    }
                    placeholder="Ask a question about this course..."
                    rows={4}
                    style={{
                      width: "100%",
                      padding: 12,
                      resize: "vertical",
                    }}
                  />

                  <button
                    type="submit"
                    disabled={
                      courseAILoading ||
                      !courseAISelected ||
                      !courseAIQuestion.trim()
                    }
                    style={{ marginTop: 12 }}
                  >
                    {courseAILoading ? "Thinking..." : "Ask Course AI"}
                  </button>
                </form>

                {courseAIError && (
                  <div style={{ marginTop: 16 }}>
                    {courseAIError}
                  </div>
                )}

                {courseAIAnswer && (
                  <div style={{ marginTop: 20 }}>
                    <h4>AI Answer</h4>
                    <div>{courseAIAnswer}</div>
                  </div>
                )}

                {courseAISources.length > 0 && (
                  <div style={{ marginTop: 20 }}>
                    <h4>Sources</h4>
                    <ul>
                      {courseAISources.map((source, index) => (
                        <li key={source.id ?? index}>
                          {source.title ||
                            source.filename ||
                            source.name ||
                            `Course material ${index + 1}`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
          {activeTab === "results" && (
            <>
              <h2 className="student-section-title">
                Academic Results
              </h2>

              <p className="student-section-description">
                Your published course results.
              </p>

              {results.length === 0 ? (
                <EmptyState message="No results have been published yet." />
              ) : (
                <div className="student-table-wrapper">
                  <table className="student-table">
                    <thead>
                      <tr>
                        <th>Course</th>
                        <th>Total</th>
                        <th>Percentage</th>
                        <th>Grade</th>
                        <th>Point</th>
                        <th>Units</th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {results.map((result, index) => (
                        <tr
                          key={
                            result.id ??
                            result.result_id ??
                            index
                          }
                        >
                          <td>
                            {result.course_offering_id ??
                              "â€”"}
                          </td>

                          <td>
                            {result.total_score ??
                              "â€”"}
                          </td>

                          <td>
                            {result.percentage ??
                              "â€”"}
                          </td>

                          <td>
                            {result.grade || "â€”"}
                          </td>

                          <td>
                            {result.grade_point ??
                              "â€”"}
                          </td>

                          <td>
                            {result.credit_units ??
                              "â€”"}
                          </td>

                          <td>
                            <StatusBadge
                              status={result.status}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {activeTab === "attendance" && (
            <>
              <h2 className="student-section-title">
                Attendance
              </h2>

              <p className="student-section-description">
                Attendance records for your courses.
              </p>

              {attendance.length === 0 ? (
                <EmptyState message="No attendance records found." />
              ) : (
                <div className="student-table-wrapper">
                  <table className="student-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Course</th>
                        <th>Status</th>
                        <th>Note</th>
                      </tr>
                    </thead>

                    <tbody>
                      {attendance.map((record, index) => (
                        <tr
                          key={
                            record.id ??
                            index
                          }
                        >
                          <td>
                            {formatDate(
                              record.attendance_date
                            )}
                          </td>

                          <td>
                            {record.course_offering_id ??
                              "â€”"}
                          </td>

                          <td>
                            <StatusBadge
                              status={record.status}
                            />
                          </td>

                          <td>
                            {record.note || "â€”"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {activeTab === "clearance" && (
            <>
              <h2 className="student-section-title">
                Clearance
              </h2>

              <p className="student-section-description">
                Your university clearance status.
              </p>

              {clearances.length === 0 ? (
                <EmptyState message="No clearance records found." />
              ) : (
                <div className="student-table-wrapper">
                  <table className="student-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Session</th>
                        <th>Status</th>
                        <th>Payment</th>
                        <th>Submitted</th>
                        <th>Completed</th>
                      </tr>
                    </thead>

                    <tbody>
                      {clearances.map((clearance, index) => (
                        <tr
                          key={
                            clearance.id ??
                            index
                          }
                        >
                          <td>
                            {formatStatus(
                              clearance.clearance_type
                            )}
                          </td>

                          <td>
                            {clearance.academic_session_id ??
                              "â€”"}
                          </td>

                          <td>
                            <StatusBadge
                              status={clearance.status}
                            />
                          </td>

                          <td>
                            <StatusBadge
                              status={
                                clearance.payment_status
                              }
                            />
                          </td>

                          <td>
                            {formatDate(
                              clearance.submitted_at
                            )}
                          </td>

                          <td>
                            {formatDate(
                              clearance.completed_at
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}

          {activeTab === "payments" && (
            <>
              <h2 className="student-section-title">
                Payments
              </h2>

              <p className="student-section-description">
                Your university invoices and payment
                transactions.
              </p>

              {invoices.length === 0 &&
              transactions.length === 0 ? (
                <EmptyState message="No payment records found." />
              ) : (
                <>
                  {invoices.length > 0 && (
                    <div
                      className="student-table-wrapper"
                      style={{ marginBottom: 20 }}
                    >
                      <table className="student-table">
                        <thead>
                          <tr>
                            <th>Invoice</th>
                            <th>Amount</th>
                            <th>Currency</th>
                            <th>Status</th>
                            <th>Due Date</th>
                          </tr>
                        </thead>

                        <tbody>
                          {invoices.map((invoice, index) => (
                            <tr
                              key={
                                invoice.id ??
                                index
                              }
                            >
                              <td>
                                {invoice.invoice_number ||
                                  "â€”"}
                              </td>

                              <td>
                                {invoice.amount ??
                                  "â€”"}
                              </td>

                              <td>
                                {invoice.currency ||
                                  "â€”"}
                              </td>

                              <td>
                                <StatusBadge
                                  status={
                                    invoice.status
                                  }
                                />
                              </td>

                              <td>
                                {formatDate(
                                  invoice.due_date
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {transactions.length > 0 && (
                    <div className="student-table-wrapper">
                      <table className="student-table">
                        <thead>
                          <tr>
                            <th>Reference</th>
                            <th>Provider</th>
                            <th>Amount</th>
                            <th>Currency</th>
                            <th>Status</th>
                            <th>Paid</th>
                          </tr>
                        </thead>

                        <tbody>
                          {transactions.map(
                            (transaction, index) => (
                              <tr
                                key={
                                  transaction.id ??
                                  index
                                }
                              >
                                <td>
                                  {transaction.transaction_reference ||
                                    "â€”"}
                                </td>

                                <td>
                                  {transaction.provider ||
                                    "â€”"}
                                </td>

                                <td>
                                  {transaction.amount ??
                                    "â€”"}
                                </td>

                                <td>
                                  {transaction.currency ||
                                    "â€”"}
                                </td>

                                <td>
                                  <StatusBadge
                                    status={
                                      transaction.status
                                    }
                                  />
                                </td>

                                <td>
                                  {formatDate(
                                    transaction.paid_at
                                  )}
                                </td>
                              </tr>
                            )
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}
            </>
          )}

        </section>
      </div>
    </div>
  );
}


