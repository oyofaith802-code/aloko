export const API_BASE_URL = "http://127.0.0.1:8000";

export function getAuthToken() {
  return localStorage.getItem("aloko_access_token");
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem("aloko_access_token", token);
  }
}

export function clearAuthToken() {
  localStorage.removeItem("aloko_access_token");
}

export async function apiFetch(path, options = {}) {
  const response = await authFetch(`${API_BASE_URL}${path}`, options);
  const text = await response.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!response.ok) {
    throw new Error(data?.detail || data?.message || `Request failed with status ${response.status}`);
  }
  return data;
}

export async function authFetch(url, options = {}) {
  const token = getAuthToken();

  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return fetch(url, {
    ...options,
    headers,
  });
}

async function handleResponse(response, defaultMessage) {
  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      result.detail ||
      result.message ||
      defaultMessage
    );
  }

  return result;
}


// ============================================================
// AUTH
// ============================================================

export async function signup(data) {
  const response = await fetch(
    `${API_BASE_URL}/auth/signup`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  return handleResponse(response, "Signup failed");
}


export async function verifyEmail(data) {
  const response = await fetch(
    `${API_BASE_URL}/auth/verify-email`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  const result = await handleResponse(
    response,
    "Email verification failed"
  );

  if (result.access_token) {
    setAuthToken(result.access_token);
  }

  return result;
}


export async function resendVerification(email) {
  const response = await fetch(
    `${API_BASE_URL}/auth/resend-verification`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
      }),
    }
  );

  return handleResponse(
    response,
    "Could not resend verification code"
  );
}


export async function forgotPassword(data) {
  const response = await fetch(
    `${API_BASE_URL}/auth/forgot-password`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  return handleResponse(
    response,
    "Password reset request failed"
  );
}

export async function resetPassword(data) {
  const response = await fetch(
    `${API_BASE_URL}/auth/reset-password`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  return handleResponse(
    response,
    "Password reset failed"
  );
}

export async function login(data) {
  const response = await fetch(
    `${API_BASE_URL}/auth/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  const result = await handleResponse(
    response,
    "Login failed"
  );

  if (result.access_token) {
    setAuthToken(result.access_token);
  }

  return result;
}


// ============================================================
// VOICES
// ============================================================

export async function getVoices() {
  const response = await authFetch(
    `${API_BASE_URL}/voices/catalog`
  );

  return handleResponse(
    response,
    "Failed to load voices"
  );
}


export async function getVoiceLanguages() {
  const response = await authFetch(
    `${API_BASE_URL}/voices/languages`
  );

  return handleResponse(
    response,
    "Failed to load voice languages"
  );
}


export async function listVoices({
  language = "",
  country = "",
  gender = "",
} = {}) {

  const params = new URLSearchParams();

  if (language) {
    params.set("language", language);
  }

  if (country) {
    params.set("country", country);
  }

  if (gender) {
    params.set("gender", gender);
  }

  const query = params.toString();

  const url = query
    ? `${API_BASE_URL}/voices/list?${query}`
    : `${API_BASE_URL}/voices/list`;

  const response = await authFetch(url);

  return handleResponse(
    response,
    "Failed to load voice list"
  );
}


export async function generateVoice(data) {
  const response = await authFetch(
    `${API_BASE_URL}/voices/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: data.text,
        voice: data.voice,
      }),
    }
  );

  return handleResponse(
    response,
    "Voice generation failed"
  );
}


export async function getMyVoices() {
  const response = await authFetch(
    `${API_BASE_URL}/voices/me`
  );

  return handleResponse(
    response,
    "Failed to load your voices"
  );
}


export async function getMyVoice(voiceId) {
  const response = await authFetch(
    `${API_BASE_URL}/voices/me/${voiceId}`
  );

  return handleResponse(
    response,
    "Failed to load voice"
  );
}


export async function uploadVoice({
  name,
  audio,
}) {

  const formData = new FormData();

  formData.append("name", name);
  formData.append("audio", audio);

  const response = await authFetch(
    `${API_BASE_URL}/voices/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(
    response,
    "Voice upload failed"
  );
}


// ============================================================
// VIDEOS
// ============================================================

export async function generateVideo(data) {
  const response = await authFetch(
    `${API_BASE_URL}/videos/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        avatar_id: Number(data.avatar_id),
        voice_id:
          data.voice_id != null
            ? Number(data.voice_id)
            : null,
        voice: data.voice || null,
        script: data.script,
      }),
    }
  );

  return handleResponse(
    response,
    "Video generation failed"
  );
}


export async function getMyVideos() {
  const response = await authFetch(
    `${API_BASE_URL}/videos/me`
  );

  return handleResponse(
    response,
    "Failed to load your videos"
  );
}


export async function getMyVideo(videoId) {
  const response = await authFetch(
    `${API_BASE_URL}/videos/me/${videoId}`
  );

  return handleResponse(
    response,
    "Failed to load video"
  );
}


// ============================================================
// AVATARS
// ============================================================

export async function getMyAvatars() {
  const response = await authFetch(
    `${API_BASE_URL}/avatars/me`
  );

  return handleResponse(
    response,
    "Failed to load your avatars"
  );
}


export async function getAvatar(avatarId) {
  const response = await authFetch(
    `${API_BASE_URL}/avatars/${avatarId}`
  );

  return handleResponse(
    response,
    "Failed to load avatar"
  );
}


export async function uploadAvatar({
  name,
  image,
}) {

  const formData = new FormData();

  formData.append("name", name);
  formData.append("image", image);

  const response = await authFetch(
    `${API_BASE_URL}/avatars/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(
    response,
    "Avatar upload failed"
  );
}


// ============================================================
// TRANSLATOR
// ============================================================

export async function translateVoice({
  audio,
  toLanguage,
  voice,
}) {

  const formData = new FormData();

  formData.append("audio", audio);

  const params = new URLSearchParams();

  params.set("to_language", toLanguage);

  if (voice) {
    params.set("voice", voice);
  }

  const response = await authFetch(
    `${API_BASE_URL}/translator/voice?${params.toString()}`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(
    response,
    "Voice translation failed"
  );
}


export async function getTranslatorLanguages() {
  const response = await authFetch(
    `${API_BASE_URL}/translator/languages`
  );

  return handleResponse(
    response,
    "Failed to load translator languages"
  );
}


export async function getTranslatorLocales() {
  const response = await authFetch(
    `${API_BASE_URL}/translator/locales`
  );

  return handleResponse(
    response,
    "Failed to load translator locales"
  );
}


// ============================================================
// CREATOR PROJECTS
// ============================================================

export async function createProject(data) {
  const response = await authFetch(
    `${API_BASE_URL}/projects`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: data.name,
        description: data.description || null,
      }),
    }
  );

  return handleResponse(
    response,
    "Failed to create project"
  );
}


export async function getMyProjects() {
  const response = await authFetch(
    `${API_BASE_URL}/projects`
  );

  return handleResponse(
    response,
    "Failed to load projects"
  );
}


export async function getProject(projectId) {
  const response = await authFetch(
    `${API_BASE_URL}/projects/${projectId}`
  );

  return handleResponse(
    response,
    "Failed to load project"
  );
}


export async function updateProject(
  projectId,
  data
) {

  const response = await authFetch(
    `${API_BASE_URL}/projects/${projectId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  return handleResponse(
    response,
    "Failed to update project"
  );
}


export async function deleteProject(projectId) {
  const response = await authFetch(
    `${API_BASE_URL}/projects/${projectId}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(
    response,
    "Failed to delete project"
  );
}


// ============================================================
// CREATOR SCENES
// ============================================================

export async function createScene(
  projectId,
  data = {}
) {

  const response = await authFetch(
    `${API_BASE_URL}/projects/${projectId}/scenes`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        script: data.script ?? null,
        avatar_id:
          data.avatar_id != null
            ? Number(data.avatar_id)
            : null,
        voice_id:
          data.voice_id != null
            ? Number(data.voice_id)
            : null,
        action: data.action ?? null,
        environment: data.environment ?? null,
        camera: data.camera ?? null,
        transition: data.transition ?? null,
        captions_enabled:
          data.captions_enabled ?? true,
        background_music:
          data.background_music ?? null,
      }),
    }
  );

  return handleResponse(
    response,
    "Failed to create scene"
  );
}


export async function updateScene(
  projectId,
  sceneId,
  data
) {

  const response = await authFetch(
    `${API_BASE_URL}/projects/${projectId}/scenes/${sceneId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  return handleResponse(
    response,
    "Failed to update scene"
  );
}


export async function deleteScene(
  projectId,
  sceneId
) {

  const response = await authFetch(
    `${API_BASE_URL}/projects/${projectId}/scenes/${sceneId}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(
    response,
    "Failed to delete scene"
  );
}


// ============================================================
// CREATOR RENDER
// ============================================================

export async function renderProject(projectId) {
  const response = await authFetch(
    `${API_BASE_URL}/projects/${projectId}/render`,
    {
      method: "POST",
    }
  );

  return handleResponse(
    response,
    "Failed to render project"
  );
}


export function getMediaUrl(path) {
  if (!path) {
    return "";
  }

  if (
    path.startsWith("http://") ||
    path.startsWith("https://")
  ) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}


// ============================================================
// AI DIRECTOR
// ============================================================

export async function generateAIDirector(data) {

  const payload =
    typeof data === "string"
      ? {
          idea: data,
        }
      : {
          idea: data?.idea || "",
          voice_mode:
            data?.voice_mode || "auto",
          voice_id:
            data?.voice_id != null
              ? Number(data.voice_id)
              : null,
          builtin_voice:
            data?.builtin_voice || null,
          avatar_mode:
            data?.avatar_mode || "auto",
          avatar_id:
            data?.avatar_id != null
              ? Number(data.avatar_id)
              : null,
        };

  const response = await authFetch(
    `${API_BASE_URL}/ai-director/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to generate AI Director project"
  );
}


// ============================================================
// BUSINESS AI
// ============================================================

export async function getBusinessWorkspaces() {
  const response = await authFetch(
    `${API_BASE_URL}/business/workspaces`
  );

  return handleResponse(
    response,
    "Failed to load business workspaces"
  );
}


export async function createBusinessWorkspace(data) {
  const response = await authFetch(
    `${API_BASE_URL}/business/workspaces`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: data?.name,
        description: data?.description || null,
      }),
    }
  );

  return handleResponse(
    response,
    "Failed to create business workspace"
  );
}


export async function getBusinessWorkspace(
  workspaceId
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/workspaces/${workspaceId}`
  );

  return handleResponse(
    response,
    "Failed to load business workspace"
  );
}


export async function getBusinessDatasets(
  workspaceId
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/datasets?workspace_id=${Number(workspaceId)}`
  );

  return handleResponse(
    response,
    "Failed to load business datasets"
  );
}


export async function getBusinessDataset(
  workspaceId,
  datasetId
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/datasets/${Number(datasetId)}`
  );

  return handleResponse(
    response,
    "Failed to load business dataset"
  );
}


export async function uploadBusinessDataset(
  workspaceId,
  file
) {

  const formData = new FormData();

  formData.append("file", file);

  const response = await authFetch(
    `${API_BASE_URL}/business/datasets/upload?workspace_id=${Number(workspaceId)}`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(
    response,
    "Failed to upload business dataset"
  );
}


export async function askBusinessAI(
  workspaceId,
  question
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/analysis/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        workspace_id: Number(workspaceId),
        question,
      }),
    }
  );

  return handleResponse(
    response,
    "Business analysis failed"
  );
}


export async function getBusinessMemory(
  workspaceId
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/workspaces/${Number(workspaceId)}/memory`
  );

  return handleResponse(
    response,
    "Failed to load business memory"
  );
}


export async function getBusinessReports(
  workspaceId
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/reports?workspace_id=${Number(workspaceId)}`
  );

  return handleResponse(
    response,
    "Failed to load business reports"
  );
}


export async function getBusinessReport(
  workspaceId,
  reportId
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/reports/${Number(reportId)}`
  );

  return handleResponse(
    response,
    "Failed to load business report"
  );
}


export async function generateBusinessReport(
  data
) {

  const response = await authFetch(
    `${API_BASE_URL}/business/reports/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        workspace_id: Number(data.workspace_id),
        title:
          data.title ||
          "Business Analysis Report",
        question:
          data.question || null,
        memory_id:
          data.memory_id != null
            ? Number(data.memory_id)
            : null,
      }),
    }
  );

  return handleResponse(
    response,
    "Failed to generate business report"
  );
}
// ============================================================
// UNIVERSITY ADMIN â€” PORTAL INTEGRATION
// ============================================================

export async function getUniversityPortalConfigs(universityId) {
  const response = await authFetch(
    `${API_BASE_URL}/university/admin/portal/configs/${Number(universityId)}`
  );

  return handleResponse(
    response,
    "Failed to load university portal configurations"
  );
}


export async function getUniversityPortalSummary(
  universityId,
  portalConfigId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/admin/portal/summary/${Number(
      universityId
    )}/${Number(portalConfigId)}`
  );

  return handleResponse(
    response,
    "Failed to load portal summary"
  );
}


export async function getUniversityPortalSyncJobs(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/admin/portal/sync/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load portal sync history"
  );
}


export async function getUniversityPortalSchedules(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/admin/portal/schedules/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load portal schedules"
  );
}


export async function getUniversityPortalWebhooks(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/admin/portal/webhooks/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load portal webhooks"
  );
}


export async function getUniversityPortalLogs(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/admin/portal/logs/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load portal integration logs"
  );
}

// University Lecturer API
export async function getLecturerMe() {
  return apiFetch('/university/lecturer/me');
}

export async function onboardLecturer(payload) {
  return apiFetch('/university/lecturer/onboard', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function getLecturerDashboard() {
  return apiFetch('/university/lecturer/dashboard');
}

export async function getLecturerCourses() {
  return apiFetch('/university/lecturer/courses');
}

export async function uploadLecturerCourseDocument(
  courseOfferingId,
  file,
  title = ""
) {
  const formData = new FormData();

  formData.append("file", file);

  if (title && title.trim()) {
    formData.append("title", title.trim());
  }

  const response = await authFetch(
    `${API_BASE_URL}/university/lecturer/courses/${Number(courseOfferingId)}/documents`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(
    response,
    "Failed to upload course document"
  );
}

export async function getLecturerCourseDocuments(
  courseOfferingId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/lecturer/courses/${Number(courseOfferingId)}/documents`
  );

  return handleResponse(
    response,
    "Failed to load course documents"
  );
}
export async function getLecturerCourseStudents(courseOfferingId) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/students`);
}

export async function addLecturerStudent(courseOfferingId, payload) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/students`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getLecturerCourseAssessments(courseOfferingId) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/assessments`);
}

export async function createLecturerAssessment(courseOfferingId, payload) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/assessments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function updateLecturerAssessment(courseOfferingId, assessmentId, payload) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/assessments/${assessmentId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteLecturerAssessment(courseOfferingId, assessmentId) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/assessments/${assessmentId}`, {
    method: "DELETE",
  });
}


export async function getLecturerCourseAttendance(courseOfferingId) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/attendance`);
}

export async function markLecturerAttendance(courseOfferingId, payload) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/attendance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function bulkMarkLecturerAttendance(courseOfferingId, payload) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/attendance/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function updateLecturerAttendance(courseOfferingId, attendanceId, payload) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/attendance/${attendanceId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function getLecturerAttendanceReport(courseOfferingId, threshold = 75) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/attendance/report?threshold=${threshold}`);
}

export async function getLecturerLowAttendance(courseOfferingId, threshold = 75) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/attendance/low?threshold=${threshold}`);
}

export async function getLecturerCourseScores(courseOfferingId) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/scores`);
}

export async function downloadLecturerCourseResults(courseOfferingId, format = "csv") {
  const response = await authFetch(
    `${API_BASE_URL}/university/lecturer/courses/${courseOfferingId}/results/export?format=${encodeURIComponent(format)}`
  );

  if (!response.ok) {
    const text = await response.text();
    let message = "Failed to export results";
    try {
      const data = text ? JSON.parse(text) : {};
      message = data?.detail || data?.message || message;
    } catch {}
    throw new Error(message);
  }

  const blob = await response.blob();

  const extension = format === "xlsx" ? "xlsx" : format;
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `course-results-${courseOfferingId}.${extension}`;
  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(url);
}

export async function saveLecturerStudentScore(courseOfferingId, payload) {
  return apiFetch(`/university/lecturer/courses/${courseOfferingId}/scores`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ============================================================
// UNIVERSITY AI MARKING
// ============================================================

export async function uploadQuestionPaper(
  assessmentId,
  universityId,
  file
) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await authFetch(
    `${API_BASE_URL}/university/ai-marking/assessments/${Number(
      assessmentId
    )}/upload-question-paper?university_id=${Number(universityId)}`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(
    response,
    "Failed to upload question paper"
  );
}


export async function uploadStudentAnswerPapers(
  assessmentId,
  universityId,
  files
) {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await authFetch(
    `${API_BASE_URL}/university/ai-marking/assessments/${Number(
      assessmentId
    )}/upload-answers?university_id=${Number(universityId)}`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(
    response,
    "Failed to upload student answer papers"
  );
}


export async function runAIMarking(
  assessmentId,
  universityId,
  submissionIds
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/ai-marking/assessments/${Number(
      assessmentId
    )}/run-marking?university_id=${Number(universityId)}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        submission_ids: submissionIds.map((id) => Number(id)),
      }),
    }
  );

  return handleResponse(
    response,
    "Failed to start AI marking"
  );
}


export async function getAIMarkingResults(
  jobId,
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/ai-marking/jobs/${Number(
      jobId
    )}/results?university_id=${Number(universityId)}`
  );

  return handleResponse(
    response,
    "Failed to load AI marking results"
  );
}


export async function matchAIMarkingSubmission(submissionId, universityId, studentId) {
  const params = new URLSearchParams({
    university_id: String(Number(universityId)),
    student_id: String(Number(studentId)),
  });

  const response = await authFetch(
    `${API_BASE_URL}/university/ai-marking/submissions/${Number(submissionId)}/match-student?${params.toString()}`,
    { method: "POST" }
  );

  return handleResponse(response, "Failed to match answer paper to student");
}

export async function reviewAIMarkingResult(
  resultId,
  {
    universityId,
    lecturerId,
    approved,
    lecturerScore,
    lecturerComment,
  }
) {
  const params = new URLSearchParams({
    university_id: String(Number(universityId)),
    lecturer_id: String(Number(lecturerId)),
    approved: String(Boolean(approved)),
  });

  if (lecturerScore !== undefined && lecturerScore !== null) {
    params.set("lecturer_score", String(lecturerScore));
  }

  if (
    lecturerComment !== undefined &&
    lecturerComment !== null
  ) {
    params.set("lecturer_comment", lecturerComment);
  }

  const response = await authFetch(
    `${API_BASE_URL}/university/ai-marking/results/${Number(
      resultId
    )}/review?${params.toString()}`,
    {
      method: "POST",
    }
  );

  return handleResponse(
    response,
    "Failed to review AI marking result"
  );
}


// ============================================================
// UNIVERSITY SCHOOL PORTAL â€” LINK / CONFIGURATION
// ============================================================

export async function createSchoolPortal(payload) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/configs`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to link school portal"
  );
}


export async function updateSchoolPortal(
  portalConfigId,
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/configs/${Number(
      portalConfigId
    )}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to update school portal"
  );
}


export async function activateSchoolPortal(
  universityId,
  portalConfigId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/configs/${Number(
      universityId
    )}/${Number(portalConfigId)}/activate`,
    {
      method: "POST",
    }
  );

  return handleResponse(
    response,
    "Failed to activate school portal"
  );
}


export async function deactivateSchoolPortal(
  universityId,
  portalConfigId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/configs/${Number(
      universityId
    )}/${Number(portalConfigId)}/deactivate`,
    {
      method: "POST",
    }
  );

  return handleResponse(
    response,
    "Failed to deactivate school portal"
  );
}


export async function testSchoolPortal(
  universityId,
  portalConfigId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/configs/${Number(
      universityId
    )}/${Number(portalConfigId)}/test`,
    {
      method: "POST",
    }
  );

  return handleResponse(
    response,
    "Failed to test school portal connection"
  );
}


// ============================================================
// UNIVERSITY PORTAL â€” SYNC
// ============================================================

export async function createPortalSync(payload) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/sync`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create portal sync"
  );
}


export async function startPortalSync(
  universityId,
  syncId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/sync/${Number(
      universityId
    )}/${Number(syncId)}/start`,
    {
      method: "POST",
    }
  );

  return handleResponse(
    response,
    "Failed to start portal sync"
  );
}


export async function getPortalSyncDetail(
  universityId,
  syncId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/sync/${Number(
      universityId
    )}/${Number(syncId)}`
  );

  return handleResponse(
    response,
    "Failed to load portal sync"
  );
}


export async function getRetryablePortalSyncs(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/portal/sync/${Number(
      universityId
    )}/retryable`
  );

  return handleResponse(
    response,
    "Failed to load retryable portal syncs"
  );
}


// ============================================================
// CLEARANCE CONFIGURATION
// ============================================================

export async function createClearanceConfig(payload) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/config`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create clearance configuration"
  );
}


export async function getClearanceConfig(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/config/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load clearance configuration"
  );
}


export async function updateClearanceConfig(
  universityId,
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/config/${Number(
      universityId
    )}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to update clearance configuration"
  );
}


// ============================================================
// CLEARANCE STAGES
// ============================================================

export async function createClearanceStage(payload) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/stages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create clearance stage"
  );
}


export async function getClearanceStages(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/stages/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load clearance stages"
  );
}


export async function updateClearanceStage(
  stageId,
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/stages/${Number(
      stageId
    )}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to update clearance stage"
  );
}


export async function deleteClearanceStage(
  stageId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/stages/${Number(
      stageId
    )}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(
    response,
    "Failed to delete clearance stage"
  );
}


// ============================================================
// CLEARANCE REQUIREMENTS
// ============================================================

export async function createClearanceRequirement(
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/requirements`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create clearance requirement"
  );
}


export async function getClearanceRequirements(
  stageId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/requirements/${Number(
      stageId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load clearance requirements"
  );
}


// ============================================================
// STUDENT CLEARANCE
// ============================================================

export async function createStudentClearance(
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/students`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create student clearance"
  );
}


export async function askStudentCourseAI(courseOfferingId, question) {
  const response = await authFetch(
    `${API_BASE_URL}/university/student/courses/${Number(courseOfferingId)}/ask`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }
  );

  return handleResponse(response, "Failed to answer course question");
}


export async function downloadStudentCourseDocument(
  courseOfferingId,
  documentId,
  filename
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/student/courses/${Number(
      courseOfferingId
    )}/documents/${Number(documentId)}/download`
  );

  if (!response.ok) {
    const result = await response.json().catch(() => ({}));
    throw new Error(
      result.detail ||
      result.message ||
      "Failed to download course material"
    );
  }

  const blob = await response.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = blobUrl;
  link.download = filename || "course-material";
  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(blobUrl);
}
export async function getStudentCourseDocuments(courseOfferingId) {
  const response = await authFetch(
    `${API_BASE_URL}/university/student/courses/${Number(
      courseOfferingId
    )}/documents`
  );

  return handleResponse(
    response,
    "Failed to load course materials"
  );
}

export function getStudentCourseDocumentDownloadUrl(
  courseOfferingId,
  documentId
) {
  return `${API_BASE_URL}/university/student/courses/${Number(
    courseOfferingId
  )}/documents/${Number(documentId)}/download`;
}
export async function getStudentClearance(
  universityId,
  studentId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/students/${Number(
      universityId
    )}/${Number(studentId)}`
  );

  return handleResponse(
    response,
    "Failed to load student clearance"
  );
}


export async function getUniversityClearances(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/students/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load university clearances"
  );
}


export async function submitClearance(payload) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/submit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to submit clearance"
  );
}


export async function approveClearanceStage(
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/approve-stage`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to approve clearance stage"
  );
}


export async function rejectClearanceStage(
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/reject-stage`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to reject clearance stage"
  );
}


export async function getClearanceProgress(
  universityId,
  studentClearanceId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/progress/${Number(
      universityId
    )}/${Number(studentClearanceId)}`
  );

  return handleResponse(
    response,
    "Failed to load clearance progress"
  );
}


export async function finalizeClearance(
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/clearance/finalize`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to finalize clearance"
  );
}


// ============================================================
// UNIVERSITY PAYMENTS
// ============================================================

export async function createPaymentConfig(payload) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/config`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create payment configuration"
  );
}


export async function getPaymentConfig(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/config/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load payment configuration"
  );
}


export async function updatePaymentConfig(
  universityId,
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/config/${Number(
      universityId
    )}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to update payment configuration"
  );
}


export async function createUniversityFee(payload) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/fees`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create university fee"
  );
}


export async function getUniversityFees(
  universityId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/fees/${Number(
      universityId
    )}`
  );

  return handleResponse(
    response,
    "Failed to load university fees"
  );
}


export async function deleteUniversityFee(
  feeId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/fees/${Number(
      feeId
    )}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(
    response,
    "Failed to delete university fee"
  );
}


export async function createUniversityInvoice(
  payload
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/invoices`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to create invoice"
  );
}


export async function getStudentInvoices(
  studentId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/students/${Number(
      studentId
    )}/invoices`
  );

  return handleResponse(
    response,
    "Failed to load student invoices"
  );
}


export async function verifyClearancePayment(
  clearanceId,
  invoiceId
) {
  const response = await authFetch(
    `${API_BASE_URL}/university/payments/clearance/verify-payment`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        clearance_id: Number(clearanceId),
        invoice_id: Number(invoiceId),
      }),
    }
  );

  return handleResponse(
    response,
    "Failed to verify clearance payment"
  );
}

export async function previewLecturerStudentImport(courseOfferingId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await authFetch(
    `${API_BASE_URL}/university/lecturer/courses/${Number(courseOfferingId)}/students/import/preview`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(response, "Failed to preview student import");
}

export async function importLecturerStudents(courseOfferingId, file, updateExisting = true) {
  const formData = new FormData();

  formData.append("file", file);
  formData.append("update_existing", String(Boolean(updateExisting)));

  const response = await authFetch(
    `${API_BASE_URL}/university/lecturer/courses/${Number(courseOfferingId)}/students/import`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(response, "Failed to import students");
}





