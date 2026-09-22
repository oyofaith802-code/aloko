import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import "./App.css";
import "./BusinessAI.css";
import UniversityAdmin from "./UniversityAdmin";
import LecturerDashboard from "./LecturerDashboard";
import StudentDashboard from "./StudentDashboard";

import {
  API_BASE_URL,

  signup,
  login,
  verifyEmail,
  resendVerification,
  forgotPassword,
  resetPassword,
  clearAuthToken,

  getVoices,
  generateVoice,
  generateVideo,

  getMyAvatars,
  uploadAvatar,
  getMyVoices,
  uploadVoice,

  createProject,
  getMyProjects,
  getProject,
  createScene,
  updateScene,
  deleteScene,
  renderProject,
  getMediaUrl,

  translateVoice,
  getTranslatorLanguages,
  getTranslatorLocales,
  generateAIDirector,

  getBusinessWorkspaces,
  createBusinessWorkspace,
  getBusinessWorkspace,
  getBusinessDatasets,
  getBusinessDataset,
  uploadBusinessDataset,
  askBusinessAI,
  getBusinessMemory,
  getBusinessReports,
  getBusinessReport,
  generateBusinessReport,
  getLecturerMe,
  onboardLecturer,
} from "./api";


/* =========================================================
   FREE ACCESS EMAILS
=========================================================

   These accounts are reserved for permanent free access
   when subscriptions are added later.

   IMPORTANT:
   This is intentionally not used as a subscription
   security check yet. Subscription enforcement will be
   implemented on the backend later.
========================================================= */

const FREE_ACCESS_EMAILS = new Set([
  "solomonenamudu@gmail.com",
  "lilkhalifa322@gmail.com",
]);


/* =========================================================
   LANGUAGE NAMES
========================================================= */

const LANGUAGE_NAMES = {
  en: "English",
  fr: "French",
  de: "German",
  es: "Spanish",
  it: "Italian",
  pt: "Portuguese",
  ar: "Arabic",
  hi: "Hindi",
  zh: "Chinese",
  ja: "Japanese",
  ko: "Korean",
  ru: "Russian",
  tr: "Turkish",
  nl: "Dutch",
  pl: "Polish",
  sv: "Swedish",
  da: "Danish",
  no: "Norwegian",
  nb: "Norwegian",
  fi: "Finnish",
  cs: "Czech",
  el: "Greek",
  he: "Hebrew",
  id: "Indonesian",
  vi: "Vietnamese",
  th: "Thai",
  uk: "Ukrainian",
  bn: "Bengali",
  ms: "Malay",
  fa: "Persian",
  sw: "Swahili",
  ro: "Romanian",
  sk: "Slovak",
  sl: "Slovenian",
  hr: "Croatian",
  hu: "Hungarian",
  mk: "Macedonian",
  ne: "Nepali",
  ps: "Pashto",
  ta: "Tamil",
  te: "Telugu",
  jv: "Javanese",
  zu: "Zulu",
  af: "Afrikaans",
};


/* =========================================================
   COUNTRY NAMES
========================================================= */

const COUNTRY_NAMES = {
  US: "United States",
  GB: "United Kingdom",
  IN: "India",
  AU: "Australia",
  CA: "Canada",
  NG: "Nigeria",
  IE: "Ireland",
  NZ: "New Zealand",
  ZA: "South Africa",
  SG: "Singapore",
  PH: "Philippines",
  MY: "Malaysia",
  HK: "Hong Kong",
  CN: "China",
  JP: "Japan",
  KR: "South Korea",
  DE: "Germany",
  FR: "France",
  ES: "Spain",
  IT: "Italy",
  BR: "Brazil",
  PT: "Portugal",
  MX: "Mexico",
  AR: "Argentina",
  BO: "Bolivia",
  CL: "Chile",
  CO: "Colombia",
  CR: "Costa Rica",
  CU: "Cuba",
  DO: "Dominican Republic",
  EC: "Ecuador",
  GQ: "Equatorial Guinea",
  GT: "Guatemala",
  HN: "Honduras",
  NI: "Nicaragua",
  PA: "Panama",
  PE: "Peru",
  PR: "Puerto Rico",
  PY: "Paraguay",
  SV: "El Salvador",
  UY: "Uruguay",
  VE: "Venezuela",
  BE: "Belgium",
  CH: "Switzerland",
  AT: "Austria",
  AE: "United Arab Emirates",
  BH: "Bahrain",
  DZ: "Algeria",
  EG: "Egypt",
  IQ: "Iraq",
  JO: "Jordan",
  KW: "Kuwait",
  LB: "Lebanon",
  LY: "Libya",
  MA: "Morocco",
  OM: "Oman",
  QA: "Qatar",
  SA: "Saudi Arabia",
  SY: "Syria",
  TN: "Tunisia",
  YE: "Yemen",
  IL: "Israel",
  RU: "Russia",
  TR: "Turkey",
  NL: "Netherlands",
  PL: "Poland",
  SE: "Sweden",
  DK: "Denmark",
  NO: "Norway",
  FI: "Finland",
  UA: "Ukraine",
  GR: "Greece",
  TH: "Thailand",
  VN: "Vietnam",
  KE: "Kenya",
  TZ: "Tanzania",
  GH: "Ghana",
  BD: "Bangladesh",
  IR: "Iran",
  CZ: "Czech Republic",
  SK: "Slovakia",
  SI: "Slovenia",
  HR: "Croatia",
  HU: "Hungary",
  MK: "North Macedonia",
  NP: "Nepal",
  AF: "Afghanistan",
};


/* =========================================================
   VOICE STYLES
========================================================= */

const STYLE_OPTIONS = [
  "Natural",
  "Friendly",
  "Professional",
  "News Presenter",
  "Narrator",
  "Energetic",
  "Calm",
];


/* =========================================================
   HELPERS
========================================================= */

function getLanguageName(code) {
  return (
    LANGUAGE_NAMES[code] ||
    code?.toUpperCase() ||
    ""
  );
}


function getCountryName(code) {
  return COUNTRY_NAMES[code] || code || "";
}


function getAccentName(accent) {
  if (!accent) {
    return "";
  }

  const parts = accent.split("-");

  if (parts.length < 2) {
    return accent;
  }

  return `${getCountryName(parts[1])} ${getLanguageName(parts[0])}`;
}


function getVoiceStyle(voice) {
  const text = `
    ${voice.name || ""}
    ${voice.tts_voice || ""}
    ${(voice.personalities || []).join(" ")}
    ${(voice.content_categories || []).join(" ")}
  `.toLowerCase();

  if (
    text.includes("news") ||
    text.includes("newscast") ||
    text.includes("newsreader")
  ) {
    return "News Presenter";
  }

  if (
    text.includes("friendly") ||
    text.includes("warm") ||
    text.includes("cheerful") ||
    text.includes("pleasant")
  ) {
    return "Friendly";
  }

  if (
    text.includes("business") ||
    text.includes("professional") ||
    text.includes("corporate")
  ) {
    return "Professional";
  }

  if (
    text.includes("narration") ||
    text.includes("narrator") ||
    text.includes("storytelling")
  ) {
    return "Narrator";
  }

  if (
    text.includes("energetic") ||
    text.includes("excited") ||
    text.includes("enthusiastic")
  ) {
    return "Energetic";
  }

  if (
    text.includes("calm") ||
    text.includes("relaxed") ||
    text.includes("soothing")
  ) {
    return "Calm";
  }

  return "Natural";
}


function getAvatarImageUrl(imageUrl) {
  if (!imageUrl) {
    return "";
  }

  if (
    imageUrl.startsWith("http://") ||
    imageUrl.startsWith("https://")
  ) {
    return imageUrl;
  }

  const cleanPath = imageUrl
    .replaceAll("\\", "/")
    .replace(/^\/+/, "");

  return `${API_BASE_URL}/${cleanPath}`;
}


function isFreeAccessEmail(email) {
  return FREE_ACCESS_EMAILS.has(
    String(email || "")
      .trim()
      .toLowerCase()
  );
}


/* =========================================================
   ALOKO SVG ASSISTANT
========================================================= */

function AlokoAssistant({
  size = 110,
}) {
  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        flexShrink: 0,
      }}
      aria-label="Aloko AI assistant"
    >
      <svg
        viewBox="0 0 120 120"
        width="100%"
        height="100%"
      >
        <defs>
          <linearGradient
            id="alokoGradientMain"
            x1="0"
            y1="0"
            x2="1"
            y2="1"
          >
            <stop
              offset="0%"
              stopColor="#8d95ff"
            />

            <stop
              offset="100%"
              stopColor="#555fd5"
            />
          </linearGradient>
        </defs>

        <circle
          cx="60"
          cy="60"
          r="52"
          fill="url(#alokoGradientMain)"
        />

        <circle
          cx="42"
          cy="48"
          r="8"
          fill="white"
        />

        <circle
          cx="78"
          cy="48"
          r="8"
          fill="white"
        />

        <circle
          cx="42"
          cy="48"
          r="3"
          fill="#202438"
        />

        <circle
          cx="78"
          cy="48"
          r="3"
          fill="#202438"
        />

        <path
          d="M38 72 Q60 88 82 72"
          fill="none"
          stroke="white"
          strokeWidth="5"
          strokeLinecap="round"
        />

        <path
          d="M37 22 Q60 8 83 22"
          fill="none"
          stroke="white"
          strokeWidth="5"
          strokeLinecap="round"
        />

        <circle
          cx="11"
          cy="60"
          r="4"
          fill="#8d95ff"
        />

        <circle
          cx="109"
          cy="60"
          r="4"
          fill="#8d95ff"
        />
      </svg>
    </div>
  );
}



/* =========================================================
   BUSINESS AI WORKSPACE
========================================================= */

function BusinessAIWorkspace({ onBack }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [workspace, setWorkspace] = useState(null);
  const [workspaceId, setWorkspaceId] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceDescription, setWorkspaceDescription] = useState("");
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);

  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [question, setQuestion] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [asking, setAsking] = useState(false);

  const [memory, setMemory] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadWorkspaceData = async (id) => {
    if (!id) return;
    setError("");
    try {
      const [ws, ds, mem, reps] = await Promise.all([
        getBusinessWorkspace(id),
        getBusinessDatasets(id),
        getBusinessMemory(id),
        getBusinessReports(id),
      ]);

      setWorkspace(ws?.workspace || ws || null);
      setDatasets(Array.isArray(ds) ? ds : ds?.datasets || []);
      setMemory(Array.isArray(mem) ? mem : mem?.memory || mem?.memories || []);
      setReports(Array.isArray(reps) ? reps : reps?.reports || []);
    } catch (err) {
setError(err.message || "Failed to load business workspace.");
    }
  };

  const loadWorkspaces = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getBusinessWorkspaces();
      const loaded = Array.isArray(data) ? data : data?.workspaces || [];
      setWorkspaces(loaded);

      if (loaded.length) {
        const saved = localStorage.getItem("aloko_business_workspace_id");
        const chosen = loaded.find((item) => String(item.id) === String(saved)) || loaded[0];
        setWorkspaceId(chosen.id);
        await loadWorkspaceData(chosen.id);
      }
    } catch (err) {
      setError(err.message || "Failed to load business workspaces.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const handleWorkspaceChange = async (event) => {
    const id = event.target.value;
    setWorkspaceId(id);
    setAnalysis(null);
    setSelectedDataset(null);
    localStorage.setItem("aloko_business_workspace_id", id);
    await loadWorkspaceData(id);
  };

  const handleCreateWorkspace = async (event) => {
    event.preventDefault();
    if (!workspaceName.trim()) return;
    setCreatingWorkspace(true);
    setError("");
    try {
      const data = await createBusinessWorkspace({
        name: workspaceName.trim(),
        description: workspaceDescription.trim() || null,
      });
      const created = data?.workspace || data;
      const next = [...workspaces, created].filter(Boolean);
      setWorkspaces(next);
      if (created?.id) {
        setWorkspaceId(created.id);
        localStorage.setItem("aloko_business_workspace_id", created.id);
        await loadWorkspaceData(created.id);
      }
      setWorkspaceName("");
      setWorkspaceDescription("");
      setNotice("Business workspace created successfully.");
    } catch (err) {
      setError(err.message || "Failed to create workspace.");
    } finally {
      setCreatingWorkspace(false);
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !workspaceId) return;

    setUploading(true);
    setError("");
    setNotice("");
    try {
      const data = await uploadBusinessDataset(workspaceId, file);
      const uploaded = data?.dataset;
      if (uploaded) {
        setDatasets((current) => [uploaded, ...current]);
        setSelectedDataset(uploaded);
      } else {
        await loadWorkspaceData(workspaceId);
      }
      setNotice(data?.message || "Dataset uploaded successfully.");
      setTab("datasets");
    } catch (err) {
      setError(err.message || "Dataset upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleDatasetOpen = async (dataset) => {
    setError("");
    try {
      const data = await getBusinessDataset(workspaceId, dataset.id);
      setSelectedDataset(data?.dataset || data || dataset);
    } catch (err) {
      setError(err.message || "Failed to load dataset details.");
    }
  };

  const handleAsk = async (event) => {
    event.preventDefault();
    if (!workspaceId || !question.trim()) return;

    setAsking(true);
    setError("");
    setNotice("");
    try {
      const data = await askBusinessAI(workspaceId, question.trim());
      setAnalysis(data);
      setQuestion("");
      setTab("analysis");
      const refreshed = await getBusinessMemory(workspaceId);
      setMemory(Array.isArray(refreshed) ? refreshed : refreshed?.memory || refreshed?.memories || []);
    } catch (err) {
      setError(err.message || "Business analysis failed.");
    } finally {
      setAsking(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!workspaceId) return;
    const memoryId = analysis?.memory_id || null;
    if (!memoryId && !memory.length) {
      setError("Ask Aloko a business question before generating a report.");
      return;
    }

    setGeneratingReport(true);
    setError("");
    try {
      const data = await generateBusinessReport({
        workspace_id: workspaceId,
        title: "Aloko Business Analysis Report",
        question: analysis?.question || null,
        memory_id: memoryId || memory[0]?.id || null,
      });
      const report = data?.report;
      if (report) {
        setSelectedReport(report);
        setReports((current) => [report, ...current]);
      }
      setNotice("Business report generated successfully.");
      setTab("reports");
    } catch (err) {
      setError(err.message || "Failed to generate business report.");
    } finally {
      setGeneratingReport(false);
    }
  };

  const openReport = async (report) => {
    setError("");
    try {
      const data = await getBusinessReport(workspaceId, report.id);
      setSelectedReport(data?.report || data || report);
    } catch (err) {
      setError(err.message || "Failed to load report.");
    }
  };

  const tableRows = analysis?.rows || analysis?.chart?.data || [];
  const columns = tableRows.length && typeof tableRows[0] === "object"
    ? Object.keys(tableRows[0])
    : [];

  const numericColumns = columns.filter((column) =>
    tableRows.some((row) => typeof row?.[column] === "number" && Number.isFinite(row[column]))
  );

  const chartType = analysis?.chart?.type || "table";
  const chartRows = tableRows.slice(0, 12);
  const chartValueColumn = numericColumns[0];
  const chartMax = chartValueColumn
    ? Math.max(...chartRows.map((row) => Number(row?.[chartValueColumn]) || 0), 1)
    : 1;

  const qualityScores = datasets
    .map((dataset) => dataset?.profile?.data_quality?.quality_score ?? dataset?.data_quality?.quality_score)
    .filter((value) => typeof value === "number");
  const averageQuality = qualityScores.length
    ? Math.round(qualityScores.reduce((sum, value) => sum + value, 0) / qualityScores.length)
    : null;
  const totalRows = datasets.reduce((sum, dataset) => sum + (Number(dataset.row_count) || 0), 0);
  const tabItems = [
    ["overview", "Overview"],
    ["datasets", "Datasets"],
    ["ask", "Ask Aloko"],
    ["analysis", "Analysis"],
    ["reports", "Reports"],
    ["memory", "Memory"],
  ];

  if (loading) {
    return (
      <div className="app">
        <main className="business-page">
          <section className="business-loading">
            <div className="spinner" />
            <h2>Opening Business AI...</h2>
            <p>Loading your workspaces, datasets and business memory.</p>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="navbar">
        <div className="logo clickable" onClick={onBack}>Aloko</div>
        <nav>
          <button onClick={onBack}>Creator</button>
          <button className="nav-active">Business AI</button>
        </nav>
        <div className="business-nav-badge">INTELLIGENCE</div>
      </header>

      <main className="business-page">
        <div className="business-topbar">
          <button className="back-button clickable" onClick={onBack}> Back to Aloko</button>
          <div className="business-title-wrap">
            <p className="eyebrow">ALOKO BUSINESS AI</p>
            <h1>Business Intelligence Workspace</h1>
            <p>Upload business data, ask questions in plain language, discover metrics and generate reports.</p>
          </div>
          <div className="business-workspace-control">
            <span>WORKSPACE</span>
            <select value={workspaceId} onChange={handleWorkspaceChange}>
              {workspaces.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
          </div>
        </div>

        {error && <div className="error business-message">{error}</div>}
        {notice && <div className="business-notice">{notice}</div>}

        {!workspaces.length ? (
          <section className="business-empty-state">
            <div className="business-empty-icon">ðŸ¢</div>
            <h2>Create your first business workspace</h2>
            <p>Keep datasets, analyses, reports and business memory together in one isolated workspace.</p>
            <form className="business-create-form" onSubmit={handleCreateWorkspace}>
              <input value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} placeholder="Company or workspace name" maxLength={255} />
              <input value={workspaceDescription} onChange={(e) => setWorkspaceDescription(e.target.value)} placeholder="Optional description" />
              <button className="generate-button" disabled={creatingWorkspace || !workspaceName.trim()}>{creatingWorkspace ? "Creating..." : "Create Workspace"}</button>
            </form>
          </section>
        ) : (
          <>
            <div className="business-tabs">
              {tabItems.map(([value, label]) => (
                <button key={value} className={tab === value ? "business-tab active" : "business-tab"} onClick={() => setTab(value)}>{label}</button>
              ))}
            </div>

            {tab === "overview" && (
              <>
                <section className="business-hero-card">
                  <div>
                    <span className="result-label">BUSINESS INTELLIGENCE</span>
                    <h2>{workspace?.name || "Your business workspace"}</h2>
                    <p>{workspace?.description || "Your central place for business data, analysis, metrics and reports."}</p>
                  </div>
                  <label className="business-upload-cta">
                    {uploading ? "Uploading..." : "ï¼‹ Upload Dataset"}
                    <input type="file" accept=".csv,.xlsx,.xls,.pdf,.docx" onChange={handleUpload} disabled={uploading} />
                  </label>
                </section>

                <section className="business-kpi-grid">
                  <div className="business-kpi"><span>DATASETS</span><strong>{datasets.length}</strong><small>Ready sources</small></div>
                  <div className="business-kpi"><span>TOTAL ROWS</span><strong>{totalRows.toLocaleString()}</strong><small>Across tabular datasets</small></div>
                  <div className="business-kpi"><span>ANALYSES</span><strong>{memory.length}</strong><small>Saved business questions</small></div>
                  <div className="business-kpi"><span>REPORTS</span><strong>{reports.length}</strong><small>Generated reports</small></div>
                  <div className="business-kpi"><span>DATA QUALITY</span><strong>{averageQuality == null ? "-" : `${averageQuality}%`}</strong><small>Average quality score</small></div>
                </section>

                <section className="business-grid-2">
                  <div className="business-panel">
                    <div className="business-panel-heading"><div><span className="result-label">DATA INTELLIGENCE</span><h3>Recent datasets</h3></div><button onClick={() => setTab("datasets")}>View all </button></div>
                    {datasets.slice(0, 5).map((dataset) => (
                      <button className="business-list-row" key={dataset.id} onClick={() => { handleDatasetOpen(dataset); setTab("datasets"); }}>
                        <span className="business-list-icon">{dataset.source_type === "pdf" || dataset.source_type === "docx" ? "" : ""}</span>
                        <span><strong>{dataset.name}</strong><small>{dataset.original_filename || dataset.source_type}</small></span>
                        <em>{dataset.row_count ? Number(dataset.row_count).toLocaleString() : "Document"}</em>
                      </button>
                    ))}
                    {!datasets.length && <p className="business-muted">Upload your first dataset to begin.</p>}
                  </div>

                  <div className="business-panel">
                    <div className="business-panel-heading"><div><span className="result-label">ASK ALOKO</span><h3>What do you want to know?</h3></div></div>
                    <form onSubmit={handleAsk} className="business-ask-mini">
                      <textarea value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Which products generate the most revenue?" maxLength={2000} />
                      <button className="generate-button" disabled={asking || !question.trim()}>{asking ? "Analyzing..." : "Analyze Business "}</button>
                    </form>
                  </div>
                </section>
              </>
            )}

            {tab === "datasets" && (
              <section className="business-section-stack">
                <div className="business-panel-heading business-section-heading"><div><span className="result-label">DATASETS</span><h2>Your business data</h2><p>CSV, Excel, PDF and DOCX ingestion is available in this workspace.</p></div><label className="business-upload-cta">{uploading ? "Uploading..." : "ï¼‹ Upload Dataset"}<input type="file" accept=".csv,.xlsx,.xls,.pdf,.docx" onChange={handleUpload} disabled={uploading} /></label></div>
                <div className="business-dataset-grid">
                  {datasets.map((dataset) => (
                    <button className="business-dataset-card" key={dataset.id} onClick={() => handleDatasetOpen(dataset)}>
                      <div className="business-dataset-card-top"><span className="business-file-icon">{dataset.source_type === "pdf" || dataset.source_type === "docx" ? "" : ""}</span><span className="business-status">{dataset.status}</span></div>
                      <h3>{dataset.name}</h3>
                      <p>{dataset.original_filename}</p>
                      <div className="business-dataset-meta"><span>{dataset.source_type?.toUpperCase()}</span><span>{dataset.row_count ? `${Number(dataset.row_count).toLocaleString()} rows` : "Document"}</span></div>
                    </button>
                  ))}
                </div>
                {selectedDataset && (
                  <div className="business-panel business-detail-panel">
                    <div className="business-panel-heading"><div><span className="result-label">DATASET DETAILS</span><h3>{selectedDataset.name}</h3></div><button onClick={() => setSelectedDataset(null)}>Close</button></div>
                    <div className="business-detail-grid"><div><span>Source</span><strong>{selectedDataset.source_type?.toUpperCase()}</strong></div><div><span>Rows</span><strong>{selectedDataset.row_count ? Number(selectedDataset.row_count).toLocaleString() : "-"}</strong></div><div><span>Status</span><strong>{selectedDataset.status}</strong></div><div><span>Table</span><strong>{selectedDataset.table_name || "Document"}</strong></div></div>
                    {selectedDataset.data_quality && <div className="business-quality-box"><h4>Data quality</h4><p>Quality score: <strong>{selectedDataset.data_quality.quality_score ?? "-"}</strong></p><pre>{JSON.stringify(selectedDataset.data_quality, null, 2)}</pre></div>}
                    {selectedDataset.schema && <div className="business-schema-box"><h4>Schema</h4><pre>{JSON.stringify(selectedDataset.schema, null, 2)}</pre></div>}
                  </div>
                )}
              </section>
            )}

            {tab === "ask" && (
              <section className="business-ask-layout">
                <div className="business-panel business-ask-panel">
                  <span className="result-label">ASK ALOKO</span>
                  <h2>Ask a business question</h2>
                  <p>Aloko will translate your question into a safe read-only query, analyze the result, select useful metrics and choose a visualization.</p>
                  <form onSubmit={handleAsk}>
                    <textarea className="business-question-box" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Example: What are our top 10 countries by sales?" maxLength={2000} />
                    <div className="business-question-footer"><span>{question.length} / 2000</span><button className="generate-button" disabled={asking || !question.trim()}>{asking ? "Analyzing business data..." : "Ask Aloko "}</button></div>
                  </form>
                  <div className="business-suggestions"><button onClick={() => setQuestion("Which products generate the most revenue?")}>Top products</button><button onClick={() => setQuestion("What are our best customers?")}>Best customers</button><button onClick={() => setQuestion("Give me a monthly business summary.")}>Monthly summary</button><button onClick={() => setQuestion("Which region is performing poorly?")}>Regional performance</button></div>
                </div>
              </section>
            )}

            {tab === "analysis" && (
              <section className="business-section-stack">
                {!analysis ? (
                  <div className="business-empty-state"><div className="business-empty-icon"></div><h2>No analysis selected</h2><p>Ask Aloko a business question to see the result here.</p><button className="generate-button" onClick={() => setTab("ask")}>Ask Aloko </button></div>
                ) : (
                  <>
                    <div className="business-analysis-header"><div><span className="result-label">BUSINESS ANALYSIS</span><h2>{analysis.question}</h2><p>{analysis.answerable === false ? analysis.reason : "Analysis completed from your workspace data."}</p></div><button className="generate-button" onClick={handleGenerateReport} disabled={generatingReport}>{generatingReport ? "Generating report..." : "Generate Report"}</button></div>
                    {analysis.answerable !== false && (
                      <>
                        <div className="business-answer-card"><span className="result-label">ALOKO'S ANSWER</span><p>{analysis.answer}</p></div>
                        <div className="business-kpi-grid analysis-kpis">
                          {(analysis.metrics || analysis.selected_metrics || []).slice(0, 6).map((metric, index) => <div className="business-kpi" key={`${metric.name || "metric"}-${index}`}><span>{metric.name || "METRIC"}</span><strong>{metric.value ?? metric.result ?? "-"}</strong><small>{metric.description || `Confidence ${metric.confidence ?? "-"}`}</small></div>)}
                        </div>
                        {(analysis.key_findings || []).length > 0 && <div className="business-panel"><span className="result-label">KEY FINDINGS</span><ul className="business-findings">{analysis.key_findings.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
                        {analysis.chart && analysis.chart.type !== "none" && (
                          <div className="business-panel"><div className="business-panel-heading"><div><span className="result-label">VISUALIZATION</span><h3>{chartType.replaceAll("_", " ").toUpperCase()}</h3></div><span className="business-chart-reason">{analysis.chart_decision?.reason || "Selected by Aloko Chart Intelligence"}</span></div>
                            {chartValueColumn && chartRows.length > 0 && chartType !== "table" ? <div className="business-chart"><div className="business-chart-bars">{chartRows.map((row, index) => <div className="business-bar-item" key={index}><div className="business-bar-label">{String(row[columns[0]] ?? index + 1).slice(0, 28)}</div><div className="business-bar-track"><div className="business-bar-fill" style={{ width: `${Math.max(3, (Number(row[chartValueColumn]) || 0) / chartMax * 100)}%` }} /></div><strong>{String(row[chartValueColumn])}</strong></div>)}</div></div> : <p className="business-muted">The selected visualization is best represented by the result table.</p>}
                          </div>
                        )}
                        <div className="business-panel"><div className="business-panel-heading"><div><span className="result-label">QUERY RESULT</span><h3>{(analysis.rows || []).length.toLocaleString()} rows</h3></div></div><div className="business-table-wrap"><table><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{(analysis.rows || []).slice(0, 100).map((row, index) => <tr key={index}>{columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}</tr>)}</tbody></table></div></div>
                        <details className="business-sql"><summary>View generated SQL</summary><pre>{analysis.sql || "No SQL returned."}</pre></details>
                      </>
                    )}
                  </>
                )}
              </section>
            )}

            {tab === "reports" && (
              <section className="business-section-stack">
                <div className="business-panel-heading business-section-heading"><div><span className="result-label">REPORTS</span><h2>Business reports</h2><p>Turn completed analyses into structured business reports.</p></div><button className="generate-button" onClick={handleGenerateReport} disabled={generatingReport || (!analysis && !memory.length)}>{generatingReport ? "Generating..." : "ï¼‹ Generate Report"}</button></div>
                <div className="business-report-grid">
                  {reports.map((report) => <button className="business-report-card" key={report.id} onClick={() => openReport(report)}><span className="business-file-icon"></span><h3>{report.title}</h3><p>{report.question || "Business analysis report"}</p><small>{report.status}  -  {report.created_at ? new Date(report.created_at).toLocaleString() : ""}</small></button>)}
                </div>
                {selectedReport && <div className="business-panel business-detail-panel"><div className="business-panel-heading"><div><span className="result-label">REPORT</span><h3>{selectedReport.title}</h3></div><button onClick={() => setSelectedReport(null)}>Close</button></div><div className="business-report-content">{selectedReport.content?.answer && <div className="business-answer-card"><span className="result-label">EXECUTIVE ANSWER</span><p>{selectedReport.content.answer}</p></div>}<pre>{JSON.stringify(selectedReport.content || selectedReport, null, 2)}</pre></div></div>}
              </section>
            )}

            {tab === "memory" && (
              <section className="business-section-stack">
                <div className="business-panel-heading business-section-heading"><div><span className="result-label">WORKSPACE MEMORY</span><h2>Business intelligence history</h2><p>Aloko keeps completed questions and analysis references in this workspace.</p></div></div>
                <div className="business-memory-list">
                  {memory.map((item) => <button className="business-memory-card" key={item.id} onClick={() => { setAnalysis({ success: true, answerable: true, question: item.question, answer: item.ai_answer, sql: item.sql_query, memory_id: item.id, rows: (() => { try { return JSON.parse(item.result_summary || "{}").rows || []; } catch { return []; } })(), summary: (() => { try { return JSON.parse(item.result_summary || "{}"); } catch { return {}; } })(), chart: { type: item.chart_type || "table", data: [] }, metrics: [], selected_metrics: [], key_findings: [], caveats: [] }); setTab("analysis"); }}><span className="business-history-icon">ðŸ§ </span><span><strong>{item.question}</strong><small>{item.ai_answer || "Analysis saved"}</small></span><em>{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</em></button>)}
                  {!memory.length && <div className="business-empty-state"><div className="business-empty-icon">ðŸ§ </div><h2>Your business memory is empty</h2><p>Completed analyses will appear here.</p></div>}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

/* =========================================================
   APP
========================================================= */

function App() {

  /* =======================================================
     AUTH USER
  ======================================================= */

  const [user, setUser] = useState(() => {
    try {
      const saved =
        localStorage.getItem(
          "aloko_user"
        );

      return saved
        ? JSON.parse(saved)
        : null;

    } catch {
      return null;
    }
  });


  const userEmail =
    user?.email || "";


  /* =======================================================
     AUTH STATE
  ======================================================= */

  const [authMode, setAuthMode] =
    useState("signup");

  const [authStep, setAuthStep] =
    useState("form");

  const [authEmail, setAuthEmail] =
    useState("");

  const [authPassword, setAuthPassword] =
    useState("");

  const [verificationCode, setVerificationCode] =
    useState("");

  const [authLoading, setAuthLoading] =
    useState(false);

  const [authError, setAuthError] =
    useState("");

  const [resetToken, setResetToken] =
    useState("");

  const [resetPasswordValue, setResetPasswordValue] =
    useState("");

  const [resetPasswordConfirm, setResetPasswordConfirm] =
    useState("");

  const [resetSuccess, setResetSuccess] =
    useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("reset_token");

    if (token) {
      setResetToken(token);
      setAuthMode("reset");
      setAuthStep("form");
setAuthError("");
      setResetSuccess("");
    }
  }, []);


  /* =======================================================
     PAGE
  ======================================================= */

  const [page, setPage] =
    useState(
      user &&
      localStorage.getItem(
        "aloko_onboarding_pending"
      ) === "true"
        ? "welcome"
        : "home"
    );

  const [lecturerOnboarding, setLecturerOnboarding] = useState(false);
  const [lecturerOnboardingLoading, setLecturerOnboardingLoading] = useState(false);
  const [lecturerOnboardingError, setLecturerOnboardingError] = useState("");
  const [lecturerForm, setLecturerForm] = useState({ first_name: "", middle_name: "", last_name: "", title: "Lecturer", academic_rank: "Lecturer", specialization: "", phone: "" });


  async function openIndependentLecturer() {
    setLecturerOnboardingError("");
    try {
      await getLecturerMe();
      setPage("university-lecturer");
    } catch (err) {
      if ((err?.message || "").includes("not linked to a university lecturer record")) {
        setLecturerOnboarding(true); setPage("university-lecturer");
        return;
      }
      setLecturerOnboardingError(err?.message || "Unable to open lecturer workspace.");
      setLecturerOnboarding(true); setPage("university-lecturer");
    }
  }

  async function submitLecturerOnboarding() {
    if (lecturerOnboardingLoading) return;
    if (!lecturerForm.first_name.trim() || !lecturerForm.last_name.trim()) {
      setLecturerOnboardingError("First name and last name are required.");
      return;
    }
    setLecturerOnboardingLoading(true);
    setLecturerOnboardingError("");
    try {
      await onboardLecturer({
        first_name: lecturerForm.first_name.trim(),
        middle_name: lecturerForm.middle_name.trim() || null,
        last_name: lecturerForm.last_name.trim(),
        title: lecturerForm.title.trim() || "Lecturer",
        academic_rank: lecturerForm.academic_rank.trim() || "Lecturer",
        specialization: lecturerForm.specialization.trim() || null,
        phone: lecturerForm.phone.trim() || null,
      });
      setLecturerOnboarding(false);
      setPage("university-lecturer");
    } catch (err) {
      setLecturerOnboardingError(err?.message || "Unable to create lecturer workspace.");
    } finally {
      setLecturerOnboardingLoading(false);
    }
  }

  /* =======================================================
     VOICES
  ======================================================= */

  const [voices, setVoices] =
    useState([]);

  const [loadingVoices, setLoadingVoices] =
    useState(false);

  const [selectedLanguage, setSelectedLanguage] =
    useState("");

  const [selectedCountry, setSelectedCountry] =
    useState("");

  const [selectedAccent, setSelectedAccent] =
    useState("");

  const [selectedGender, setSelectedGender] =
    useState("");

  const [selectedStyle, setSelectedStyle] =
    useState("");

  const [selectedVoice, setSelectedVoice] =
    useState("");

  const [previewingVoice, setPreviewingVoice] =
    useState(false);

  const [previewAudioUrl, setPreviewAudioUrl] =
    useState("");


  /* =======================================================
     SCRIPT / GENERATION
  ======================================================= */

  const [script, setScript] =
    useState("");

  const [generating, setGenerating] =
    useState(false);

  const [result, setResult] =
    useState(null);

  const [error, setError] =
    useState("");

  /* =======================================================
     CREATOR STUDIO
  ======================================================= */

  if (page === "video") {
    const readyPersonalVoices = creatorMyVoices.filter(
      v =>
        v.voice_type === "custom" &&
        v.status === "ready" &&
        v.provider_voice_id
    );

    const selectedAvatar = avatars.find(
      a => Number(a.id) === Number(selectedAvatarId)
    );

    const builtInVoices = [
      { value: "en-US-AriaNeural", label: "Aria" },
      { value: "en-US-GuyNeural", label: "Guy" },
      { value: "en-US-JennyNeural", label: "Jenny" },
      { value: "en-US-SaraNeural", label: "Sara" },
    ];

    const saveSceneField = (sceneId, field, value) => {
      setCreatorScenes(prev =>
        prev.map(scene =>
          scene.id === sceneId
            ? { ...scene, [field]: value }
            : scene
        )
      );

      saveCreatorScene(sceneId, {
        [field]: value,
      });
    };

    return (
      <div className="app">
        {renderNavbar("video")}

        <main
          style={{
            maxWidth: "1250px",
            margin: "0 auto",
            padding: "35px 20px 70px",
          }}
        >
          <button
            className="back-button clickable"
            onClick={() => setPage("home")}
          >
            Back
          </button>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
              gap: "20px",
              flexWrap: "wrap",
              marginBottom: "30px",
            }}
          >
            <div>
              <p className="eyebrow">ALOKO CREATOR STUDIO</p>

              <h1>Create your AI video</h1>

              <p>
                Build your video scene by scene. Each scene can have
                its own avatar, voice, script and visual settings.
              </p>
            </div>

            <button
              className="generate-button"
              onClick={createNewCreatorProject}
              disabled={creatorSaving || creatorLoading}
            >
              + New Project
            </button>
          </div>

          {error && <div className="error">{error}</div>}

          {creatorLoading ? (
            <section
              className="coming-card"
              style={{
                textAlign: "center",
                padding: "60px 25px",
              }}
            >
              <div className="spinner"></div>

              <h2>Opening Creator Studio...</h2>

              <p>
                Loading your projects and scenes.
              </p>
            </section>
          ) : (
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "minmax(0, 1.4fr) minmax(320px, 0.8fr)",
                gap: "25px",
                alignItems: "start",
              }}
            >
              <section
                className="creator-panel"
                style={{ padding: "25px" }}
              >

                {/* PROJECT */}

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "15px",
                    marginBottom: "25px",
                    flexWrap: "wrap",
                  }}
                >
                  <div>
                    <span className="result-label">
                      PROJECT
                    </span>

                    <h2 style={{ margin: "5px 0 0" }}>
                      {creatorProject?.name || "My AI Video"}
                    </h2>
                  </div>

                  {creatorProjects.length > 1 && (
                    <select
                      value={creatorProject?.id || ""}
                      onChange={e =>
                        loadCreatorProject(
                          Number(e.target.value)
                        )
                      }
                    >
                      {creatorProjects.map(project => (
                        <option
                          key={project.id}
                          value={project.id}
                        >
                          {project.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {/* DEFAULT AVATAR */}

                <div className="form-section">
                  <label>
                    Default Avatar
                  </label>

                  {avatars.length === 0 ? (
                    <div
                      className="avatar-box"
                      style={{ padding: "20px" }}
                    >
                      <strong>
                        Create an avatar first.
                      </strong>

                      <p>
                        Your avatar will be used for
                        talking-video scenes.
                      </p>

                      <button
                        className="generate-button"
                        onClick={() => setPage("avatar")}
                      >
                        Create Avatar
                      </button>
                    </div>
                  ) : (
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns:
                          "repeat(auto-fill, minmax(150px, 1fr))",
                        gap: "12px",
                      }}
                    >
                      {avatars.map(avatar => (
                        <button
                          key={avatar.id}
                          type="button"
                          onClick={() =>
                            setSelectedAvatarId(avatar.id)
                          }
                          style={{
                            border:
                              Number(selectedAvatarId) ===
                              Number(avatar.id)
                                ? "2px solid #8d95ff"
                                : "1px solid rgba(255,255,255,0.12)",
                            borderRadius: "14px",
                            padding: "8px",
                            background: "transparent",
                            cursor: "pointer",
                            textAlign: "left",
                          }}
                        >
                          <img
                            src={getAvatarImageUrl(
                              avatar.image_url
                            )}
                            alt={
                              avatar.name ||
                              "Avatar"
                            }
                            style={{
                              width: "100%",
                              aspectRatio: "1 / 1",
                              objectFit: "cover",
                              borderRadius: "10px",
                              display: "block",
                            }}
                          />

                          <strong
                            style={{
                              display: "block",
                              marginTop: "8px",
                            }}
                          >
                            {avatar.name ||
                              "My Avatar"}
                          </strong>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* SCENES */}

                <div
                  className="form-section"
                  style={{ marginTop: "32px" }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "15px",
                    }}
                  >
                    <div>
                      <label>
                        Scenes
                      </label>

                      <p style={{ marginTop: "5px" }}>
                        Every scene has independent
                        avatar, voice and visual settings.
                      </p>
                    </div>

                    <button
                      type="button"
                      className="generate-button"
                      onClick={addCreatorScene}
                      disabled={
                        !creatorProject ||
                        creatorSaving
                      }
                    >
                      + Add Scene
                    </button>
                  </div>

                  {creatorScenes.length === 0 ? (
                    <div
                      className="preview-empty"
                      style={{ marginTop: "20px" }}
                    >
                      <div className="preview-icon"></div>

                      <h2>
                        No scenes yet
                      </h2>

                      <p>
                        Add your first scene and
                        write the script Aloko should speak.
                      </p>
                    </div>
                  ) : (
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "18px",
                        marginTop: "20px",
                      }}
                    >
                      {creatorScenes.map(scene => {

                        const sceneAvatar =
                          avatars.find(
                            a =>
                              Number(a.id) ===
                              Number(scene.avatar_id)
                          );

                        const sceneVoiceMode =
                          scene.voice_id
                            ? "personal"
                            : "built_in";

                        return (
                          <div
                            key={scene.id}
                            style={{
                              border:
                                "1px solid rgba(255,255,255,0.12)",
                              borderRadius: "16px",
                              padding: "18px",
                            }}
                          >

                            {/* HEADER */}

                            <div
                              style={{
                                display: "flex",
                                justifyContent:
                                  "space-between",
                                alignItems: "center",
                                marginBottom: "18px",
                              }}
                            >
                              <strong>
                                Scene {scene.scene_order}
                              </strong>

                              <button
                                type="button"
                                onClick={() =>
                                  removeCreatorScene(
                                    scene.id
                                  )
                                }
                                disabled={
                                  creatorSaving
                                }
                                style={{
                                  border: "none",
                                  background:
                                    "transparent",
                                  cursor: "pointer",
                                  color: "#ff8f8f",
                                }}
                              >
                                Delete
                              </button>
                            </div>

                            {/* AVATAR */}

                            <div
                              style={{
                                marginBottom: "18px",
                              }}
                            >
                              <label>
                                Avatar
                              </label>

                              <select
                                value={
                                  scene.avatar_id ||
                                  ""
                                }
                                onChange={e => {
                                  const value =
                                    e.target.value
                                      ? Number(
                                          e.target.value
                                        )
                                      : null;

                                  saveSceneField(
                                    scene.id,
                                    "avatar_id",
                                    value
                                  );
                                }}
                                style={{
                                  width: "100%",
                                  marginTop: "8px",
                                }}
                              >
                                <option value="">
                                  Select avatar
                                </option>

                                {avatars.map(
                                  avatar => (
                                    <option
                                      key={avatar.id}
                                      value={avatar.id}
                                    >
                                      {avatar.name ||
                                        "My Avatar"}
                                    </option>
                                  )
                                )}
                              </select>

                              {sceneAvatar && (
                                <div
                                  style={{
                                    marginTop: "8px",
                                    fontSize: "12px",
                                    opacity: 0.7,
                                  }}
                                >
                                  Using:{" "}
                                  {sceneAvatar.name ||
                                    "My Avatar"}
                                </div>
                              )}
                            </div>

                            {/* VOICE */}

                            <div
                              style={{
                                marginBottom: "18px",
                              }}
                            >
                              <label>
                                Voice
                              </label>

                              <select
                                value={sceneVoiceMode}
                                onChange={e => {
                                  const mode =
                                    e.target.value;

                                  if (
                                    mode ===
                                    "personal"
                                  ) {
                                    saveCreatorScene(
                                      scene.id,
                                      {
                                        voice_id:
                                          readyPersonalVoices[0]
                                            ?.id || null,
                                        voice: null,
                                      }
                                    );

                                    setCreatorScenes(
                                      prev =>
                                        prev.map(
                                          item =>
                                            item.id ===
                                            scene.id
                                              ? {
                                                  ...item,
                                                  voice_id:
                                                    readyPersonalVoices[0]
                                                      ?.id ||
                                                    null,
                                                  voice: null,
                                                }
                                              : item
                                        )
                                    );
                                  } else {
                                    saveCreatorScene(
                                      scene.id,
                                      {
                                        voice_id:
                                          null,
                                        voice:
                                          builtInVoices[0]
                                            .value,
                                      }
                                    );

                                    setCreatorScenes(
                                      prev =>
                                        prev.map(
                                          item =>
                                            item.id ===
                                            scene.id
                                              ? {
                                                  ...item,
                                                  voice_id:
                                                    null,
                                                  voice:
                                                    builtInVoices[0]
                                                      .value,
                                                }
                                              : item
                                        )
                                    );
                                  }
                                }}
                                style={{
                                  width: "100%",
                                  marginTop: "8px",
                                }}
                              >
                                <option value="built_in">
                                  Aloko Built-in Voice
                                </option>

                                <option
                                  value="personal"
                                  disabled={
                                    !readyPersonalVoices.length
                                  }
                                >
                                  My Personal Voice
                                </option>
                              </select>

                              {sceneVoiceMode ===
                                "personal" && (
                                <select
                                  value={
                                    scene.voice_id ||
                                    ""
                                  }
                                  onChange={e => {
                                    const value =
                                      e.target.value
                                        ? Number(
                                            e.target
                                              .value
                                          )
                                        : null;

                                    saveCreatorScene(
                                      scene.id,
                                      {
                                        voice_id:
                                          value,
                                        voice:
                                          null,
                                      }
                                    );

                                    setCreatorScenes(
                                      prev =>
                                        prev.map(
                                          item =>
                                            item.id ===
                                            scene.id
                                              ? {
                                                  ...item,
                                                  voice_id:
                                                    value,
                                                  voice:
                                                    null,
                                                }
                                              : item
                                        )
                                    );
                                  }}
                                  style={{
                                    width: "100%",
                                    marginTop: "8px",
                                  }}
                                >
                                  <option value="">
                                    Select personal voice
                                  </option>

                                  {readyPersonalVoices.map(
                                    voice => (
                                      <option
                                        key={voice.id}
                                        value={voice.id}
                                      >
                                        {voice.name ||
                                          "Personal Voice"}
                                      </option>
                                    )
                                  )}
                                </select>
                              )}

                              {sceneVoiceMode ===
                                "built_in" && (
                                <select
                                  value={
                                    scene.voice ||
                                    builtInVoices[0]
                                      .value
                                  }
                                  onChange={e =>
                                    saveCreatorScene(
                                      scene.id,
                                      {
                                        voice_id:
                                          null,
                                        voice:
                                          e.target.value,
                                      }
                                    )
                                  }
                                  style={{
                                    width: "100%",
                                    marginTop: "8px",
                                  }}
                                >
                                  {builtInVoices.map(
                                    voice => (
                                      <option
                                        key={
                                          voice.value
                                        }
                                        value={
                                          voice.value
                                        }
                                      >
                                        {voice.label}
                                      </option>
                                    )
                                  )}
                                </select>
                              )}
                            </div>

                            {/* SCRIPT */}

                            <div
                              style={{
                                marginBottom: "18px",
                              }}
                            >
                              <label>
                                Script
                              </label>

                              <textarea
                                value={
                                  scene.script || ""
                                }
                                onChange={e => {
                                  const value =
                                    e.target.value;

                                  setCreatorScenes(
                                    prev =>
                                      prev.map(
                                        item =>
                                          item.id ===
                                          scene.id
                                            ? {
                                                ...item,
                                                script:
                                                  value,
                                              }
                                            : item
                                      )
                                  );
                                }}
                                onBlur={e =>
                                  saveCreatorScene(
                                    scene.id,
                                    {
                                      script:
                                        e.target.value,
                                    }
                                  )
                                }
                                maxLength={5000}
                                rows={6}
                                placeholder="Write what your avatar should say in this scene..."
                                style={{
                                  width: "100%",
                                  resize: "vertical",
                                }}
                              />

                              <div
                                style={{
                                  display: "flex",
                                  justifyContent:
                                    "space-between",
                                  marginTop: "8px",
                                  fontSize: "12px",
                                  opacity: 0.65,
                                }}
                              >
                                <span>
                                  {(scene.script || "")
                                    .length}
                                  /5000
                                </span>
                              </div>
                            </div>

                            {/* VISUAL CONTROLS */}

                            <div
                              style={{
                                display: "grid",
                                gridTemplateColumns:
                                  "repeat(auto-fit, minmax(150px, 1fr))",
                                gap: "12px",
                              }}
                            >

                              <div>
                                <label>
                                  Environment
                                </label>

                                <select
                                  value={
                                    scene.environment ||
                                    ""
                                  }
                                  onChange={e =>
                                    saveSceneField(
                                      scene.id,
                                      "environment",
                                      e.target.value ||
                                        null
                                    )
                                  }
                                  style={{
                                    width: "100%",
                                    marginTop: "7px",
                                  }}
                                >
                                  <option value="">
                                    Default
                                  </option>
                                  <option value="studio">
                                    Studio
                                  </option>
                                  <option value="office">
                                    Office
                                  </option>
                                  <option value="classroom">
                                    Classroom
                                  </option>
                                  <option value="outdoor">
                                    Outdoor
                                  </option>
                                  <option value="newsroom">
                                    Newsroom
                                  </option>
                                </select>
                              </div>

                              <div>
                                <label>
                                  Camera
                                </label>

                                <select
                                  value={
                                    scene.camera ||
                                    ""
                                  }
                                  onChange={e =>
                                    saveSceneField(
                                      scene.id,
                                      "camera",
                                      e.target.value ||
                                        null
                                    )
                                  }
                                  style={{
                                    width: "100%",
                                    marginTop: "7px",
                                  }}
                                >
                                  <option value="">
                                    Default
                                  </option>
                                  <option value="close_up">
                                    Close-up
                                  </option>
                                  <option value="medium">
                                    Medium
                                  </option>
                                  <option value="wide">
                                    Wide
                                  </option>
                                </select>
                              </div>

                              <div>
                                <label>
                                  Action
                                </label>

                                <select
                                  value={
                                    scene.action ||
                                    ""
                                  }
                                  onChange={e =>
                                    saveSceneField(
                                      scene.id,
                                      "action",
                                      e.target.value ||
                                        null
                                    )
                                  }
                                  style={{
                                    width: "100%",
                                    marginTop: "7px",
                                  }}
                                >
                                  <option value="">
                                    Natural
                                  </option>
                                  <option value="talking">
                                    Talking
                                  </option>
                                  <option value="presenting">
                                    Presenting
                                  </option>
                                  <option value="explaining">
                                    Explaining
                                  </option>
                                </select>
                              </div>

                              <div>
                                <label>
                                  Transition
                                </label>

                                <select
                                  value={
                                    scene.transition ||
                                    ""
                                  }
                                  onChange={e =>
                                    saveSceneField(
                                      scene.id,
                                      "transition",
                                      e.target.value ||
                                        null
                                    )
                                  }
                                  style={{
                                    width: "100%",
                                    marginTop: "7px",
                                  }}
                                >
                                  <option value="">
                                    Cut
                                  </option>
                                  <option value="fade">
                                    Fade
                                  </option>
                                  <option value="crossfade">
                                    Crossfade
                                  </option>
                                </select>
                              </div>
                            </div>

                            {/* CAPTIONS */}

                            <label
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                                marginTop: "16px",
                                cursor: "pointer",
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={
                                  scene.captions_enabled !==
                                  false
                                }
                                onChange={e =>
                                  saveSceneField(
                                    scene.id,
                                    "captions_enabled",
                                    e.target.checked
                                  )
                                }
                              />

                              Captions
                            </label>

                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                <button
                  className="generate-button"
                  style={{
                    width: "100%",
                    marginTop: "30px",
                  }}
                  disabled={
                    creatorRenderLoading ||
                    creatorSaving ||
                    !creatorProject ||
                    !creatorScenes.length ||
                    creatorScenes.some(
                      scene =>
                        !scene.avatar_id ||
                        !scene.script?.trim() ||
                        (
                          !scene.voice_id &&
                          !scene.voice
                        )
                    )
                  }
                  onClick={handleCreatorRender}
                >
                  {creatorRenderLoading
                    ? "Rendering video..."
                    : "Generate Video"}
                </button>

                {creatorRenderError && (
                  <div
                    className="error"
                    style={{ marginTop: "15px" }}
                  >
                    {creatorRenderError}
                  </div>
                )}
              </section>

              {/* PREVIEW */}

              <section
                className="creator-panel"
                style={{
                  padding: "25px",
                  position: "sticky",
                  top: "20px",
                }}
              >
                <span className="result-label">
                  VIDEO PREVIEW
                </span>

                {creatorRenderLoading ? (
                  <div
                    className="preview-empty"
                    style={{
                      minHeight: "430px",
                    }}
                  >
                    <div className="spinner"></div>

                    <h2>
                      Creating your video
                    </h2>

                    <p>
                      Aloko is generating the
                      voice, animating the avatar
                      and combining your scenes.
                    </p>
                  </div>
                ) : creatorRenderResult?.video_url ? (
                  <div>
                    <h2 style={{ marginTop: "10px" }}>
                      Your video is ready
                    </h2>

                    <video
                      controls
                      style={{
                        width: "100%",
                        borderRadius: "14px",
                        marginTop: "15px",
                        display: "block",
                      }}
                      src={getMediaUrl(
                        creatorRenderResult.video_url
                      )}
                    />

                    <div
                      className="result-actions"
                      style={{ marginTop: "15px" }}
                    >
                      <a
                        href={getMediaUrl(
                          creatorRenderResult.video_url
                        )}
                        download
                      >
                        Download MP4
                      </a>
                    </div>
                  </div>
                ) : (
                  <div
                    className="preview-empty"
                    style={{
                      minHeight: "430px",
                    }}
                  >
                    <div className="preview-icon"></div>

                    <h2>
                      Your final video
                    </h2>

                    <p>
                      Select an avatar, configure
                      each scene and generate the
                      finished MP4.
                    </p>
                  </div>
                )}
              </section>
            </div>
          )}
        </main>
      </div>
    );
  }


  return null;
}


export default App;










