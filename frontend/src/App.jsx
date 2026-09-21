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
    useState("login");

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

  const [creatorProjects, setCreatorProjects] = useState([]);
  const [creatorProject, setCreatorProject] = useState(null);
  const [creatorScenes, setCreatorScenes] = useState([]);
  const [creatorMyVoices, setCreatorMyVoices] = useState([]);
  const [creatorProjectName, setCreatorProjectName] = useState("My AI Video");
  const [creatorLoading, setCreatorLoading] = useState(false);
  const [creatorSaving, setCreatorSaving] = useState(false);
  const [creatorVoiceType, setCreatorVoiceType] = useState("built_in");
  const [creatorSelectedPersonalVoice, setCreatorSelectedPersonalVoice] = useState("");
  const [creatorRenderLoading, setCreatorRenderLoading] = useState(false);
  const [creatorRenderResult, setCreatorRenderResult] = useState(null);
  const [creatorRenderError, setCreatorRenderError] = useState("");

  /* =======================================================
     AI DIRECTOR
  ======================================================= */
  const [aiDirectorIdea, setAiDirectorIdea] = useState("");
  const [aiDirectorLoading, setAiDirectorLoading] = useState(false);
  const [aiDirectorError, setAiDirectorError] = useState("");
  const [aiDirectorResult, setAiDirectorResult] = useState(null);
  const [aiDirectorVoiceMode, setAiDirectorVoiceMode] = useState("auto");
  const [aiDirectorPersonalVoice, setAiDirectorPersonalVoice] = useState("");
  const [aiDirectorBuiltinVoice, setAiDirectorBuiltinVoice] = useState("");
  const [aiDirectorAvatarMode, setAiDirectorAvatarMode] = useState("auto");
  const [aiDirectorAvatarId, setAiDirectorAvatarId] = useState("");


  /* =======================================================
     AVATAR
  ======================================================= */

  const [avatars, setAvatars] =
    useState([]);

  const [loadingAvatars, setLoadingAvatars] =
    useState(false);

  const [selectedAvatarId, setSelectedAvatarId] =
    useState("");

  const [avatarType, setAvatarType] =
    useState("");

  const [avatarName, setAvatarName] =
    useState("");

  const [avatarImage, setAvatarImage] =
    useState(null);

  const [avatarUploading, setAvatarUploading] =
    useState(false);


  /* =======================================================
     USER VOICE TEST
  ======================================================= */

  const [voiceRecording, setVoiceRecording] =
    useState(false);

  const [voiceRecordingSeconds, setVoiceRecordingSeconds] =
    useState(0);

  const [voiceTestAudioUrl, setVoiceTestAudioUrl] =
    useState("");

  const [personalVoiceRecordingBlob, setPersonalVoiceRecordingBlob] =
    useState(null);

  const [personalVoiceName, setPersonalVoiceName] =
    useState("My Personal Voice");

  const [personalVoiceUploading, setPersonalVoiceUploading] =
    useState(false);

  const voiceRecorderRef =
    useRef(null);

  const voiceChunksRef =
    useRef([]);

  const voiceTimerRef =
    useRef(null);


  /* =======================================================
     TRANSLATOR
  ======================================================= */

  const [translatorLanguages, setTranslatorLanguages] =
    useState([]);

  const [translatorLocales, setTranslatorLocales] =
    useState([]);

  const [translatorFile, setTranslatorFile] =
    useState(null);

  const [translatorTargetLanguage, setTranslatorTargetLanguage] =
    useState("en");

  const [translatorCountry, setTranslatorCountry] =
    useState("");

  const [translatorAccent, setTranslatorAccent] =
    useState("");

  const [translatorGender, setTranslatorGender] =
    useState("");

  const [translatorVoice, setTranslatorVoice] =
    useState("");

  const [translatorResult, setTranslatorResult] =
    useState(null);

  const [translatorLoading, setTranslatorLoading] =
    useState(false);

  const [translatorError, setTranslatorError] =
    useState("");

  const [translatorPreviewLoading, setTranslatorPreviewLoading] =
    useState(false);

  const [translatorPreviewAudioUrl, setTranslatorPreviewAudioUrl] =
    useState("");

  const [recording, setRecording] =
    useState(false);

  const [recordingSeconds, setRecordingSeconds] =
    useState(0);

  const mediaRecorderRef =
    useRef(null);

  const recordingChunksRef =
    useRef([]);

  const recordingTimerRef =
    useRef(null);


  /* =======================================================
     SAVE SESSION
  ======================================================= */

  function saveUserSession(data) {
    const session = {
      user_id: data.user_id,
      email: data.email,
    };

    localStorage.setItem(
      "aloko_user",
      JSON.stringify(session)
    );

    setUser(session);

    setAuthEmail("");
    setAuthPassword("");
    setVerificationCode("");
    setAuthError("");
    setAuthStep("form");
  }


  /* =======================================================
     SIGNUP / LOGIN
  ======================================================= */

  async function handleForgotPassword(event) {
    event.preventDefault();

    setAuthError("");
    setResetSuccess("");

    const email = authEmail.trim().toLowerCase();

    if (!email) {
      setAuthError("Please enter your email address.");
      return;
    }

    setAuthLoading(true);

    try {
      const data = await forgotPassword({ email });

      setResetSuccess(
        data?.message ||
        "If an account exists for this email, a password reset link will be sent."
      );
    } catch (err) {
      setAuthError(
        err?.message ||
        "Unable to process password reset request."
      );
    } finally {
      setAuthLoading(false);
    }
  }


  async function handleResetPassword(event) {
    event.preventDefault();

    setAuthError("");
    setResetSuccess("");

    if (!resetToken.trim()) {
      setAuthError("Invalid or missing password reset token.");
      return;
    }

    if (resetPasswordValue.length < 6) {
      setAuthError("Password must be at least 6 characters.");
      return;
    }

    if (resetPasswordValue !== resetPasswordConfirm) {
      setAuthError("Passwords do not match.");
      return;
    }

    setAuthLoading(true);

    try {
      await resetPassword({
        token: resetToken.trim(),
        new_password: resetPasswordValue,
      });

      setResetPasswordValue("");
      setResetPasswordConfirm("");
      setResetToken("");

      setResetSuccess(
        "Password reset successfully. You can now sign in."
      );

      setAuthMode("login");
    } catch (err) {
      setAuthError(
        err?.message ||
        "Password reset failed."
      );
    } finally {
      setAuthLoading(false);
    }
  }


  async function handleAuthSubmit(event) {
    event.preventDefault();

    setAuthError("");

    const email =
      authEmail
        .trim()
        .toLowerCase();

    if (!email) {
      setAuthError(
        "Please enter your email address."
      );

      return;
    }

    if (
      authPassword.length < 6
    ) {
      setAuthError(
        "Password must be at least 6 characters."
      );

      return;
    }

    setAuthLoading(true);

    try {

      if (authMode === "signup") {

        await signup({
          email,
          password:
            authPassword,
        });

        localStorage.setItem(
          "aloko_onboarding_pending",
          "true"
        );

        setAuthStep(
          "verification"
        );

      } else {

        const data =
          await login({
            email,
            password:
              authPassword,
          });

        saveUserSession(data);

        if (
          localStorage.getItem(
            "aloko_onboarding_pending"
          ) === "true"
        ) {
          setPage(
            "welcome"
          );
        } else {
          setPage(
            "home"
          );
        }
      }

    } catch (err) {

      setAuthError(
        err.message ||
        "Authentication failed."
      );

    } finally {

      setAuthLoading(
        false
      );
    }
  }


  /* =======================================================
     VERIFY EMAIL
  ======================================================= */

  async function handleVerifyEmail(event) {
    event.preventDefault();

    setAuthError("");

    if (
      !/^\d{6}$/.test(
        verificationCode
      )
    ) {
      setAuthError(
        "Enter the 6-digit verification code."
      );

      return;
    }

    setAuthLoading(true);

    try {

      const data =
        await verifyEmail({
          email:
            authEmail
              .trim()
              .toLowerCase(),

          code:
            verificationCode,
        });

      localStorage.setItem(
        "aloko_onboarding_pending",
        "true"
      );

      saveUserSession(data);

      setPage(
        "welcome"
      );

    } catch (err) {

      setAuthError(
        err.message ||
        "Verification failed."
      );

    } finally {

      setAuthLoading(
        false
      );
    }
  }


  /* =======================================================
     RESEND VERIFICATION
  ======================================================= */

  async function handleResendVerification() {
    setAuthError("");

    try {

      await resendVerification(
        authEmail
          .trim()
          .toLowerCase()
      );

      setAuthError(
        "A new verification code was generated. Check the backend terminal."
      );

    } catch (err) {

      setAuthError(
        err.message ||
        "Could not resend verification code."
      );
    }
  }


  function switchAuthMode(mode) {
    setAuthMode(mode);
    setAuthStep("form");
    setAuthError("");
    setAuthEmail("");
    setAuthPassword("");
    setVerificationCode("");
  }


  /* =======================================================
     LOGOUT
  ======================================================= */

  function logout() {
    clearAuthToken();

    localStorage.removeItem(
      "aloko_user"
    );

    setUser(null);

    setAvatars([]);

    setSelectedAvatarId("");

    setPage("home");
  }


  /* =======================================================
     LOAD USER AVATARS
  ======================================================= */

  useEffect(() => {

    if (!user) {
      return;
    }

    async function loadAvatars() {

      setLoadingAvatars(
        true
      );

      try {

        const data =
          await getMyAvatars();

        const loaded =
          Array.isArray(data)
            ? data
            : data.avatars || [];

        setAvatars(
          loaded
        );

        if (
          loaded.length > 0
        ) {

          const first =
            loaded[0];

          setSelectedAvatarId(
            first.id
          );
          if (!aiDirectorAvatarId) {
            setAiDirectorAvatarId(String(first.id));
          }
        }

      } catch (err) {

        if (
          err.message
            ?.toLowerCase()
            .includes("authentication")
        ) {
          logout();
          return;
        }

        setError(
          err.message
        );

      } finally {

        setLoadingAvatars(
          false
        );
      }
    }

    loadAvatars();

  }, [user]);


  /* =======================================================
     LOAD VOICES
  ======================================================= */

  useEffect(() => {

    if (!user) {
      return;
    }

    if (
      page !== "home" &&
      page !== "voice" &&
      page !== "video" &&
      page !== "translator"
    ) {
      return;
    }

    async function loadVoices() {

      setLoadingVoices(
        true
      );

      try {

        const data =
          await getVoices();

        const loaded =
          data.voices || [];

        setVoices(
          loaded
        );

        if (
          loaded.length > 0
        ) {

          const first =
            loaded[0];

          setSelectedLanguage(
            first.language || ""
          );

          setSelectedCountry(
            first.country || ""
          );

          setSelectedAccent(
            first.accent || ""
          );

          setSelectedGender(
            first.gender || ""
          );

          setSelectedVoice(
            first.tts_voice || ""
          );

          const english =
            loaded.find(
              (voice) =>
                voice.language === "en"
            );

          if (english) {
            setTranslatorVoice(
              english.tts_voice
            );
            if (!aiDirectorBuiltinVoice) {
              setAiDirectorBuiltinVoice(english.tts_voice);
            }
          }
        }

      } catch (err) {

        setError(
          err.message
        );

      } finally {

        setLoadingVoices(
          false
        );
      }
    }

    loadVoices();

  }, [page, user, aiDirectorBuiltinVoice]);


  /* =======================================================
     LOAD TRANSLATOR DATA
  ======================================================= */

  useEffect(() => {

    if (
      !user ||
      page !== "translator"
    ) {
      return;
    }

    async function loadTranslatorData() {

      setTranslatorError("");

      try {

        const [
          languageData,
          localeData,
        ] =
          await Promise.all([
            getTranslatorLanguages(),
            getTranslatorLocales(),
          ]);

        setTranslatorLanguages(
          languageData.languages || []
        );

        setTranslatorLocales(
          localeData.locales || []
        );

      } catch (err) {

        setTranslatorError(
          err.message
        );
      }
    }

    loadTranslatorData();

  }, [page, user]);


  /* =======================================================
     VOICE FILTER DATA
  ======================================================= */

  const languages =
    useMemo(() => {

      return [
        ...new Set(
          voices
            .map(
              (voice) =>
                voice.language
            )
            .filter(Boolean)
        ),
      ].sort();

    }, [voices]);


  const countries =
    useMemo(() => {

      return [
        ...new Set(
          voices
            .filter(
              (voice) =>
                !selectedLanguage ||
                voice.language ===
                  selectedLanguage
            )
            .map(
              (voice) =>
                voice.country
            )
            .filter(Boolean)
        ),
      ].sort();

    }, [
      voices,
      selectedLanguage,
    ]);


  const accents =
    useMemo(() => {

      return [
        ...new Set(
          voices
            .filter(
              (voice) =>
                (
                  !selectedLanguage ||
                  voice.language ===
                    selectedLanguage
                ) &&
                (
                  !selectedCountry ||
                  voice.country ===
                    selectedCountry
                )
            )
            .map(
              (voice) =>
                voice.accent
            )
            .filter(Boolean)
        ),
      ].sort();

    }, [
      voices,
      selectedLanguage,
      selectedCountry,
    ]);


  const filteredVoices =
    useMemo(() => {

      return voices.filter(
        (voice) =>
          (
            !selectedLanguage ||
            voice.language ===
              selectedLanguage
          ) &&
          (
            !selectedCountry ||
            voice.country ===
              selectedCountry
          ) &&
          (
            !selectedAccent ||
            voice.accent ===
              selectedAccent
          ) &&
          (
            !selectedGender ||
            voice.gender ===
              selectedGender
          ) &&
          (
            !selectedStyle ||
            getVoiceStyle(
              voice
            ) ===
              selectedStyle
          )
      );

    }, [
      voices,
      selectedLanguage,
      selectedCountry,
      selectedAccent,
      selectedGender,
      selectedStyle,
    ]);


  useEffect(() => {

    if (
      filteredVoices.length === 0
    ) {
      setSelectedVoice("");
      return;
    }

    const exists =
      filteredVoices.some(
        (voice) =>
          voice.tts_voice ===
          selectedVoice
      );

    if (!exists) {
      setSelectedVoice(
        filteredVoices[0]
          .tts_voice
      );
    }

  }, [
    filteredVoices,
    selectedVoice,
  ]);


  /* =======================================================
     VOICE FILTER HANDLERS
  ======================================================= */

  function handleLanguageChange(
    value
  ) {

    setSelectedLanguage(
      value
    );

    setSelectedCountry("");

    setSelectedAccent("");
  }


  function handleCountryChange(
    value
  ) {

    setSelectedCountry(
      value
    );

    setSelectedAccent("");
  }


  /* =======================================================
     AI VOICE PREVIEW
  ======================================================= */

  async function handlePreviewVoice() {

    if (!selectedVoice) {
      setError(
        "Please select a voice."
      );

      return;
    }

    setPreviewingVoice(
      true
    );

    setError("");

    try {

      const data =
        await generateVoice({
          text:
            "Hello, this is Aloko. This is a preview of the selected AI voice.",

          voice:
            selectedVoice,
        });

      if (!data.audio_url) {
        throw new Error(
          "Preview audio was not returned."
        );
      }

      setPreviewAudioUrl(
        `${API_BASE_URL}${data.audio_url}`
      );

    } catch (err) {

      setError(
        err.message
      );

    } finally {

      setPreviewingVoice(
        false
      );
    }
  }


  /* =======================================================
     GENERATE VOICE
  ======================================================= */

  async function handleGenerateVoice() {

    if (!script.trim()) {
      setError(
        "Please enter a script."
      );

      return;
    }

    if (!selectedVoice) {
      setError(
        "Please select a voice."
      );

      return;
    }

    setGenerating(
      true
    );

    setError("");

    setResult(null);

    try {

      const data =
        await generateVoice({
          text:
            script,

          voice:
            selectedVoice,
        });

      setResult(
        data
      );

    } catch (err) {

      setError(
        err.message
      );

    } finally {

      setGenerating(
        false
      );
    }
  }


  /* =======================================================
     CREATE IMAGE AVATAR
  ======================================================= */

  async function handleCreateAvatar() {

    setError("");

    if (!avatarType) {

      setError(
        "Choose Image Avatar or Video Avatar."
      );

      return;
    }

    if (
      avatarType === "video"
    ) {

      setError(
        "Video Avatar is coming next. Image Avatar creation is available now."
      );

      return;
    }

    if (!avatarImage) {

      setError(
        "Please select an image."
      );

      return;
    }

    setAvatarUploading(
      true
    );

    try {

      const data =
        await uploadAvatar({
          name:
            avatarName.trim() ||
            "My Avatar",

          image:
            avatarImage,
        });

      const created = {
        id:
          data.id,

        name:
          data.name,

        image_url:
          data.image_url,
      };

      setAvatars(
        previous => [
          created,
          ...previous,
        ]
      );

      setSelectedAvatarId(
        created.id
      );

      localStorage.setItem(
        "aloko_onboarding_pending",
        "true"
      );

      setPage(
        "voice-test"
      );

      setAvatarName("");

      setAvatarImage(
        null
      );

    } catch (err) {

      setError(
        err.message
      );

    } finally {

      setAvatarUploading(
        false
      );
    }
  }


  /* =======================================================
     USER VOICE TEST
  ======================================================= */

  async function startVoiceTest() {

    setError("");

    try {

      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      const recorder =
        new MediaRecorder(
          stream
        );

      voiceChunksRef.current = [];

      recorder.ondataavailable =
        (event) => {

          if (
            event.data.size > 0
          ) {
            voiceChunksRef.current.push(
              event.data
            );
          }
        };

      recorder.onstop =
        () => {

          const blob =
            new Blob(
              voiceChunksRef.current,
              {
                type:
                  recorder.mimeType ||
                  "audio/webm",
              }
            );

          const url =
            URL.createObjectURL(
              blob
            );

          setVoiceTestAudioUrl(
            url
          );

          setPersonalVoiceRecordingBlob(
            blob
          );

          stream
            .getTracks()
            .forEach(
              track =>
                track.stop()
            );
        };

      voiceRecorderRef.current =
        recorder;

      recorder.start();

      setVoiceRecording(
        true
      );

      setVoiceRecordingSeconds(
        0
      );

      voiceTimerRef.current =
        setInterval(
          () => {

            setVoiceRecordingSeconds(
              value =>
                value + 1
            );

          },
          1000
        );

    } catch {

      setError(
        "Microphone access was denied or unavailable."
      );
    }
  }


  async function saveRecordedPersonalVoice() {
    if (!personalVoiceRecordingBlob) {
      setError("Record your voice first.");
      return;
    }

    setPersonalVoiceUploading(true);
    setError("");

    try {
      const mimeType = personalVoiceRecordingBlob.type || "audio/webm";
      const extension = mimeType.includes("ogg") ? "ogg" : mimeType.includes("mp4") ? "m4a" : "webm";
      const audioFile = new File(
        [personalVoiceRecordingBlob],
        `aloko-personal-voice.${extension}`,
        { type: mimeType }
      );

      const data = await uploadVoice({
        name: personalVoiceName.trim() || "My Personal Voice",
        audio: audioFile,
      });

      await loadCreatorVoices();

      const savedVoiceId = data?.voice_id || data?.id;
      if (savedVoiceId) {
        setCreatorSelectedPersonalVoice(String(savedVoiceId));
        setAiDirectorPersonalVoice(String(savedVoiceId));
      }

      setAiDirectorVoiceMode("personal");
      setPage("home");
    } catch (err) {
      setError(err.message || "Failed to save your personal voice.");
    } finally {
      setPersonalVoiceUploading(false);
    }
  }

  function stopVoiceTest() {

    const recorder =
      voiceRecorderRef.current;

    if (
      recorder &&
      recorder.state !==
        "inactive"
    ) {
      recorder.stop();
    }

    setVoiceRecording(
      false
    );

    if (
      voiceTimerRef.current
    ) {

      clearInterval(
        voiceTimerRef.current
      );

      voiceTimerRef.current =
        null;
    }
  }


  /* =======================================================
     GENERATE CREATOR VIDEO
  ======================================================= */

  async function handleGenerateVideo() {

    if (!selectedAvatarId) {

      setPage(
        "avatar"
      );

      setError(
        "Create an avatar first."
      );

      return;
    }

    if (!script.trim()) {

      setError(
        "Please enter a script."
      );

      return;
    }

    if (!selectedVoice) {

      setError(
        "Please select a voice."
      );

      return;
    }

    setGenerating(
      true
    );

    setError("");

    setResult(null);

    try {

      const data =
        await generateVideo({

          avatar_id:
            Number(
              selectedAvatarId
            ),

          voice:
            selectedVoice,

          script:
            script,
        });

      setResult(
        data
      );

    } catch (err) {

      setError(
        err.message
      );

    } finally {

      setGenerating(
        false
      );
    }
  }


  /* =======================================================
     TRANSLATOR DATA
  ======================================================= */

  const translatorLanguageLocales =
    useMemo(() => {

      return translatorLocales.filter(
        locale =>
          locale.language ===
          translatorTargetLanguage
      );

    }, [
      translatorLocales,
      translatorTargetLanguage,
    ]);


  const translatorCountries =
    useMemo(() => {

      return [
        ...new Set(
          translatorLanguageLocales
            .map(
              locale =>
                locale.country
            )
            .filter(Boolean)
        ),
      ].sort();

    }, [
      translatorLanguageLocales,
    ]);


  const translatorAccents =
    useMemo(() => {

      return [
        ...new Set(
          translatorLanguageLocales
            .filter(
              locale =>
                !translatorCountry ||
                locale.country ===
                  translatorCountry
            )
            .map(
              locale =>
                locale.accent
            )
            .filter(Boolean)
        ),
      ].sort();

    }, [
      translatorLanguageLocales,
      translatorCountry,
    ]);


  const translatorVoices =
    useMemo(() => {

      return voices.filter(
        voice =>
          voice.language ===
            translatorTargetLanguage &&
          (
            !translatorCountry ||
            voice.country ===
              translatorCountry
          ) &&
          (
            !translatorAccent ||
            voice.accent ===
              translatorAccent
          ) &&
          (
            !translatorGender ||
            voice.gender ===
              translatorGender
          )
      );

    }, [
      voices,
      translatorTargetLanguage,
      translatorCountry,
      translatorAccent,
      translatorGender,
    ]);


  useEffect(() => {

    if (
      translatorVoices.length ===
      0
    ) {
      setTranslatorVoice("");
      return;
    }

    const exists =
      translatorVoices.some(
        voice =>
          voice.tts_voice ===
          translatorVoice
      );

    if (!exists) {

      setTranslatorVoice(
        translatorVoices[0]
          .tts_voice
      );
    }

  }, [
    translatorVoices,
    translatorVoice,
  ]);


  function clearTranslatorPreview() {

    setTranslatorPreviewAudioUrl(
      ""
    );
  }


  /* =======================================================
     TRANSLATOR RECORDING
  ======================================================= */

  async function startTranslatorRecording() {

    setTranslatorError("");

    try {

      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      const recorder =
        new MediaRecorder(
          stream
        );

      recordingChunksRef.current =
        [];

      recorder.ondataavailable =
        (event) => {

          if (
            event.data.size > 0
          ) {

            recordingChunksRef.current.push(
              event.data
            );
          }
        };

      recorder.onstop =
        () => {

          const blob =
            new Blob(
              recordingChunksRef.current,
              {
                type:
                  recorder.mimeType ||
                  "audio/webm",
              }
            );

          const file =
            new File(
              [blob],
              "aloko-recording.webm",
              {
                type:
                  recorder.mimeType ||
                  "audio/webm",
              }
            );

          setTranslatorFile(
            file
          );

          stream
            .getTracks()
            .forEach(
              track =>
                track.stop()
            );
        };

      mediaRecorderRef.current =
        recorder;

      recorder.start();

      setRecording(
        true
      );

      setRecordingSeconds(
        0
      );

      recordingTimerRef.current =
        setInterval(
          () => {

            setRecordingSeconds(
              value =>
                value + 1
            );

          },
          1000
        );

    } catch {

      setTranslatorError(
        "Microphone access was denied or unavailable."
      );
    }
  }


  function stopTranslatorRecording() {

    const recorder =
      mediaRecorderRef.current;

    if (
      recorder &&
      recorder.state !==
        "inactive"
    ) {

      recorder.stop();
    }

    setRecording(
      false
    );

    if (
      recordingTimerRef.current
    ) {

      clearInterval(
        recordingTimerRef.current
      );

      recordingTimerRef.current =
        null;
    }
  }


  /* =======================================================
     TRANSLATOR PREVIEW
  ======================================================= */

  async function handleTranslatorPreview() {

    if (!translatorVoice) {

      setTranslatorError(
        "Please select a voice."
      );

      return;
    }

    setTranslatorPreviewLoading(
      true
    );

    setTranslatorError("");

    try {

      const data =
        await generateVoice({

          text:
            "Hello, this is an Aloko voice preview.",

          voice:
            translatorVoice,
        });

      if (!data.audio_url) {

        throw new Error(
          "Preview audio was not returned."
        );
      }

      setTranslatorPreviewAudioUrl(
        `${API_BASE_URL}${data.audio_url}`
      );

    } catch (err) {

      setTranslatorError(
        err.message
      );

    } finally {

      setTranslatorPreviewLoading(
        false
      );
    }
  }


  /* =======================================================
     TRANSLATE
  ======================================================= */

  async function handleTranslateVoice() {

    if (!translatorFile) {

      setTranslatorError(
        "Please record or upload audio."
      );

      return;
    }

    if (!translatorVoice) {

      setTranslatorError(
        "Please select a target voice."
      );

      return;
    }

    setTranslatorLoading(
      true
    );

    setTranslatorError("");

    setTranslatorResult(
      null
    );

    try {

      const data =
        await translateVoice({

          audio:
            translatorFile,

          toLanguage:
            translatorTargetLanguage,

          voice:
            translatorVoice,
        });

      setTranslatorResult(
        data
      );

    } catch (err) {

      setTranslatorError(
        err.message
      );

    } finally {

      setTranslatorLoading(
        false
      );
    }
  }


  /* =======================================================
     AI DIRECTOR
  ======================================================= */
  async function handleAIDirectorGenerate() {
    const idea = aiDirectorIdea.trim();

    if (!idea) {
      setAiDirectorError("Tell Aloko what video you want to create.");
      return;
    }

    if (aiDirectorVoiceMode === "personal" && !aiDirectorPersonalVoice) {
      setAiDirectorError("Select your personal voice first.");
      return;
    }

    if (aiDirectorVoiceMode === "builtin" && !aiDirectorBuiltinVoice) {
      setAiDirectorError("Select an Aloko voice first.");
      return;
    }

    if (aiDirectorAvatarMode === "selected" && !aiDirectorAvatarId) {
      setAiDirectorError("Select an avatar first.");
      return;
    }

    setAiDirectorLoading(true);
    setAiDirectorError("");
    setAiDirectorResult(null);
    setError("");

    try {
      const data = await generateAIDirector({
        idea,
        voice_mode: aiDirectorVoiceMode,
        voice_id:
          aiDirectorVoiceMode === "personal" && aiDirectorPersonalVoice
            ? Number(aiDirectorPersonalVoice)
            : null,
        builtin_voice:
          aiDirectorVoiceMode === "builtin"
            ? aiDirectorBuiltinVoice
            : null,
        avatar_mode: aiDirectorAvatarMode,
        avatar_id:
          aiDirectorAvatarMode === "selected" && aiDirectorAvatarId
            ? Number(aiDirectorAvatarId)
            : null,
      });

      setAiDirectorResult(data);

      if (data?.project?.id) {
        await loadCreatorProjects();
        const loadedProject = await loadCreatorProject(data.project.id);
        const firstScene = loadedProject?.scenes?.[0];

        if (firstScene?.avatar_id) {
          setSelectedAvatarId(String(firstScene.avatar_id));
          setAiDirectorAvatarId(String(firstScene.avatar_id));
        }

        if (firstScene?.voice_id) {
          setCreatorVoiceType("personal");
          setCreatorSelectedPersonalVoice(String(firstScene.voice_id));
        } else if (firstScene?.voice) {
          setCreatorVoiceType("built_in");
          setSelectedVoice(firstScene.voice);
        }

        setPage("video");
      }
    } catch (err) {
      setAiDirectorError(
        err.message || "AI Director failed to create the project."
      );
    } finally {
      setAiDirectorLoading(false);
    }
  }

  /* =======================================================
     CREATOR STUDIO FUNCTIONS
  ======================================================= */

  async function loadCreatorProjects() {
    try {
      const data = await getMyProjects();
      const projects = Array.isArray(data) ? data : [];
      setCreatorProjects(projects);
      return projects;
    } catch (err) {
      setError(err.message || "Failed to load Creator projects.");
      return [];
    }
  }

  async function loadCreatorProject(projectId) {
    setCreatorLoading(true);
    setError("");
    try {
      const data = await getProject(projectId);
      setCreatorProject(data);
      setCreatorScenes(data.scenes || []);
      setCreatorProjectName(data.name || "My AI Video");
      return data;
    } catch (err) {
      setError(err.message || "Failed to load Creator project.");
      return null;
    } finally {
      setCreatorLoading(false);
    }
  }

  async function ensureCreatorProject() {
    if (creatorProject) return creatorProject;
    setCreatorLoading(true);
    setError("");
    try {
      const projects = creatorProjects.length ? creatorProjects : await loadCreatorProjects();
      if (projects.length) return await loadCreatorProject(projects[0].id);
      const project = await createProject({ name: creatorProjectName.trim() || "My AI Video" });
      setCreatorProject(project);
      setCreatorScenes([]);
      await loadCreatorProjects();
      return project;
    } catch (err) {
      setError(err.message || "Failed to open Creator Studio.");
      return null;
    } finally {
      setCreatorLoading(false);
    }
  }

  async function loadCreatorVoices() {
    try {
      const data = await getMyVoices();
      const loaded = Array.isArray(data) ? data : data?.voices || [];
      setCreatorMyVoices(loaded);
      const ready = loaded.find(v => v.voice_type === "custom" && v.status === "ready" && v.provider_voice_id);
      if (ready) {
        if (!creatorSelectedPersonalVoice) {
          setCreatorSelectedPersonalVoice(String(ready.id));
        }
        if (!aiDirectorPersonalVoice) {
          setAiDirectorPersonalVoice(String(ready.id));
        }
      }
    } catch {
      setCreatorMyVoices([]);
    }
  }

  async function createNewCreatorProject() {
    setCreatorSaving(true);
    setError("");
    try {
      const project = await createProject({ name: creatorProjectName.trim() || "My AI Video" });
      setCreatorProject(project);
      setCreatorScenes([]);
      setCreatorRenderResult(null);
      await loadCreatorProjects();
    } catch (err) {
      setError(err.message || "Failed to create project.");
    } finally {
      setCreatorSaving(false);
    }
  }

  async function addCreatorScene() {
    if (!creatorProject) {
      setError("Create or open a project first.");
      return;
    }
    setCreatorSaving(true);
    setError("");
    try {
      const scene = await createScene(creatorProject.id, {
        script: "",
        avatar_id: selectedAvatarId ? Number(selectedAvatarId) : null,
        voice_id: creatorVoiceType === "personal" && creatorSelectedPersonalVoice ? Number(creatorSelectedPersonalVoice) : null,
        captions_enabled: true,
      });
      setCreatorScenes(previous => [...previous, scene]);
    } catch (err) {
      setError(err.message || "Failed to add scene.");
    } finally {
      setCreatorSaving(false);
    }
  }

  async function saveCreatorScene(sceneId, updates) {
    if (!creatorProject) return;
    try {
      const updated = await updateScene(creatorProject.id, sceneId, updates);
      setCreatorScenes(previous => previous.map(scene => scene.id === sceneId ? updated : scene));
    } catch (err) {
      setError(err.message || "Failed to save scene.");
    }
  }

  async function removeCreatorScene(sceneId) {
    if (!creatorProject) return;
    setCreatorSaving(true);
    setError("");
    try {
      await deleteScene(creatorProject.id, sceneId);
      setCreatorScenes(previous => previous.filter(scene => scene.id !== sceneId));
    } catch (err) {
      setError(err.message || "Failed to delete scene.");
    } finally {
      setCreatorSaving(false);
    }
  }

  async function handleCreatorRender() {
    if (!creatorProject) { setError("Create or open a project first."); return; }
    if (!creatorScenes.length) { setError("Add at least one scene."); return; }
    const empty = creatorScenes.find(scene => !scene.script || !scene.script.trim());
    if (empty) { setError(`Scene ${empty.scene_order} needs a script.`); return; }
    if (!selectedAvatarId) { setError("Select an avatar first."); return; }
    if (creatorVoiceType === "personal" && !creatorSelectedPersonalVoice) { setError("Select a ready personal voice first."); return; }
    setCreatorRenderLoading(true);
    setCreatorRenderError("");
    setError("");
    setCreatorRenderResult(null);
    try {
      const data = await renderProject(creatorProject.id);
      setCreatorRenderResult(data);
    } catch (err) {
      setCreatorRenderError(err.message || "Failed to render project.");
    } finally {
      setCreatorRenderLoading(false);
    }
  }

  useEffect(() => {
    if (!user) return;
    loadCreatorVoices();
  }, [user]);

  useEffect(() => {
    if (!user || page !== "video") return;
    ensureCreatorProject();
  }, [user, page]);


  /* =======================================================
     NAVBAR
  ======================================================= */

  function renderNavbar(active) {

    return (
      <header className="navbar">

        <div
          className="logo clickable"
          onClick={() =>
            setPage(
              "home"
            )
          }
          >
          Aloko
        </div>


        <nav>

          <button
            className={
              active === "home"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setPage(
                "home"
              )
            }
          >
            Home
          </button>


          <button
            className={
              active === "voice"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setPage(
                "voice"
              )
            }
          >
            AI Voice
          </button>


          <button
            className={
              active === "translator"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setPage(
                "translator"
              )
            }
          >
            Voice Translator
          </button>


          <button
            className={
              active === "video"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setPage(
                "video"
              )
            }
          >
            Creator Video
          </button>


          <button
            className={
              active === "avatar"
                ? "nav-active"
                : ""
            }
            onClick={() =>
              setPage(
                "avatar"
              )
            }
          >
            Avatar
          </button>


          <button
            className={active === "business" ? "nav-active" : ""}
            type="button"
            onClick={() => setPage("business")}
          >
            Business
          </button>


          <button
            className={active === "university-admin" ? "nav-active" : ""}
            type="button"
            onClick={() => setPage("university-admin")}
          >
            University Admin
          </button>

          <button
            className={active === "university-lecturer" ? "nav-active" : ""}
            type="button"
            onClick={() => openIndependentLecturer()}
          >
            Lecturer
          </button>

          <button
            className={active === "university-student" ? "nav-active" : ""}
            type="button"
            onClick={() => setPage("university-student")}
          >
            Student
          </button>

          <button
            className="coming-nav-item"
            type="button"
            disabled
          >
            AI Extract
          </button>

        </nav>


        {user && (
          <div
            style={{
              marginLeft:
                "auto",

              display:
                "flex",

              alignItems:
                "center",

              gap:
                "10px",
            }}
          >

            <span
              style={{
                fontSize:
                  "12px",

                opacity:
                  0.75,
              }}
            >
              {user.email}

              {isFreeAccessEmail(
                user.email
              ) && (
                <span
                  style={{
                    marginLeft:
                      "7px",

                    color:
                      "#8d95ff",

                    fontWeight:
                      700,
                  }}
                >
                  FREE
                </span>
              )}
            </span>


            <button
              type="button"
              onClick={
                logout
              }
              style={{
                padding:
                  "8px 12px",

                border:
                  "1px solid #303542",

                borderRadius:
                  "8px",

                background:
                  "#11141b",

                color:
                  "white",

                cursor:
                  "pointer",
              }}
            >
              Logout
            </button>

          </div>
        )}

      </header>
    );
  }



  /* =======================================================
     BUSINESS AI
  ======================================================= */

  if (page === "business") {
    return <BusinessAIWorkspace onBack={() => setPage("home")} />;
  }

  /* =======================================================
     UNIVERSITY AI ADMIN
  ======================================================= */

  if (page === "university-admin") {
    return <UniversityAdmin onBack={() => setPage("home")} />;
  }

  if (page === "university-lecturer") {
    if (lecturerOnboarding) return (
      <div style={{minHeight:"100vh",padding:"40px 20px",display:"flex",justifyContent:"center",alignItems:"center"}}>
        <div style={{width:"100%",maxWidth:"620px",padding:"32px",borderRadius:"20px",background:"var(--card-bg, #fff)",boxShadow:"0 10px 40px rgba(0,0,0,0.08)"}}>
          <h1>Set up your Lecturer Workspace</h1>
          <p>Complete your lecturer profile to create your private academic workspace.</p>
          {lecturerOnboardingError && (
            <div style={{marginBottom:"16px",padding:"12px",borderRadius:"10px",color:"#b91c1c",background:"#fee2e2"}}>{lecturerOnboardingError}</div>
          )}
          <div style={{display:"grid",gap:"14px"}}>
            <input placeholder="First name *" value={lecturerForm.first_name} onChange={e => setLecturerForm({...lecturerForm, first_name:e.target.value})} />
            <input placeholder="Middle name" value={lecturerForm.middle_name} onChange={e => setLecturerForm({...lecturerForm, middle_name:e.target.value})} />
            <input placeholder="Last name *" value={lecturerForm.last_name} onChange={e => setLecturerForm({...lecturerForm, last_name:e.target.value})} />
            <input placeholder="Academic specialization" value={lecturerForm.specialization} onChange={e => setLecturerForm({...lecturerForm, specialization:e.target.value})} />
            <input placeholder="Phone number" value={lecturerForm.phone} onChange={e => setLecturerForm({...lecturerForm, phone:e.target.value})} />
          </div>
          <div style={{display:"flex",gap:"12px",marginTop:"22px"}}>
            <button type="button" onClick={() => setLecturerOnboarding(false)}>Back</button>
            <button type="button" onClick={submitLecturerOnboarding} disabled={lecturerOnboardingLoading}>
              {lecturerOnboardingLoading ? "Creating workspace..." : "Create Lecturer Workspace"}
            </button>
          </div>
        </div>
      </div>
    );

    return <LecturerDashboard onBack={() => setPage("home")} />;
  }

  if (page === "university-student") {
    return <StudentDashboard onBack={() => setPage("home")} />;
  }

  /* =======================================================
     AUTH SCREEN
  ======================================================= */

  if (!user) {

    return (
      <div
        className="app"
        style={{
          minHeight:
            "100vh",

          display:
            "flex",

          flexDirection:
            "column",
        }}
      >

        <header className="navbar">

          <div className="logo">
            Aloko
          </div>

        </header>


        <main
          style={{
            flex:
              1,

            display:
              "flex",

            justifyContent:
              "center",

            alignItems:
              "center",

            padding:
              "30px 20px",
          }}
        >

          <section
            style={{
              width:
                "100%",

              maxWidth:
                "460px",

              padding:
                "32px",

              border:
                "1px solid #282d38",

              borderRadius:
                "22px",

              background:
                "#101219",
            }}
          >

            <div
              style={{
                textAlign:
                  "center",
              }}
            >

              <AlokoAssistant
                size={90}
              />

              <p className="eyebrow">
                AI CREATION PLATFORM
              </p>

              <h1>
                {
                  authStep ===
                  "verification"
                    ? "Verify your email"
                    : authMode ===
                      "login"
                      ? "Welcome back"
                      : "Create your Aloko account"
                }
              </h1>

              <p>
                {
                  authStep ===
                  "verification"
                    ? `Enter the 6-digit code for ${authEmail}`
                    : authMode ===
                      "login"
                      ? "Sign in to continue creating with Aloko."
                      : "Create an account to start using Aloko."
                }
              </p>

            </div>


            {authError && (
              <div className="error">
                {authError}
              </div>
            )}


            {authStep ===
            "verification" ? (

              <>

                <form
                  onSubmit={
                    handleVerifyEmail
                  }
                >

                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    value={
                      verificationCode
                    }
                    onChange={
                      event =>
                        setVerificationCode(
                          event.target.value.replace(
                            /\D/g,
                            ""
                          )
                        )
                    }
                    placeholder="123456"
                    style={{
                      width:
                        "100%",

                      boxSizing:
                        "border-box",

                      textAlign:
                        "center",

                      letterSpacing:
                        "8px",

                      fontSize:
                        "24px",

                      marginTop:
                        "15px",
                    }}
                  />


                  <button
                    className="generate-button"
                    type="submit"
                    disabled={
                      authLoading
                    }
                    style={{
                      width:
                        "100%",

                      marginTop:
                        "15px",
                    }}
                  >
                    {authLoading
                      ? "Verifying..."
                      : "Verify Email"}
                  </button>

                </form>


                <button
                  type="button"
                  onClick={
                    handleResendVerification
                  }
                  style={{
                    display:
                      "block",

                    margin:
                      "18px auto 0",

                    border:
                      "none",

                    background:
                      "none",

                    color:
                      "#8d95ff",

                    cursor:
                      "pointer",
                  }}
                >
                  Resend verification code
                </button>

              </>

            ) : authMode === "forgot" ? (

              <>

                <form
                  onSubmit={
                    handleForgotPassword
                  }
                >

                  <label>
                    Email
                  </label>

                  <input
                    type="email"
                    value={
                      authEmail
                    }
                    onChange={
                      event =>
                        setAuthEmail(
                          event.target.value
                        )
                    }
                    required
                    placeholder="you@example.com"
                    style={{
                      width:
                        "100%",

                      boxSizing:
                        "border-box",

                      marginBottom:
                        "18px",
                    }}
                  />

                  <button
                    className="generate-button"
                    type="submit"
                    disabled={
                      authLoading
                    }
                    style={{
                      width:
                        "100%",
                    }}
                  >
                    {authLoading
                      ? "Sending..."
                      : "Send Reset Link"}
                  </button>

                </form>

                <button
                  type="button"
                  onClick={() => {
                    setAuthMode("login");
                    setAuthError("");
                    setResetSuccess("");
                  }}
                  style={{
                    display:
                      "block",

                    margin:
                      "18px auto 0",

                    border:
                      "none",

                    background:
                      "none",

                    color:
                      "#8d95ff",

                    cursor:
                      "pointer",
                  }}
                >
                  Back to sign in
                </button>

              </>

            ) : authMode === "reset" ? (

              <>

                <form
                  onSubmit={
                    handleResetPassword
                  }
                >

                  <label>
                    New Password
                  </label>

                  <input
                    type="password"
                    value={
                      resetPasswordValue
                    }
                    onChange={
                      event =>
                        setResetPasswordValue(
                          event.target.value
                        )
                    }
                    required
                    minLength={6}
                    placeholder="New password"
                    style={{
                      width:
                        "100%",

                      boxSizing:
                        "border-box",

                      marginBottom:
                        "15px",
                    }}
                  />

                  <label>
                    Confirm Password
                  </label>

                  <input
                    type="password"
                    value={
                      resetPasswordConfirm
                    }
                    onChange={
                      event =>
                        setResetPasswordConfirm(
                          event.target.value
                        )
                    }
                    required
                    minLength={6}
                    placeholder="Confirm new password"
                    style={{
                      width:
                        "100%",

                      boxSizing:
                        "border-box",

                      marginBottom:
                        "18px",
                    }}
                  />

                  <button
                    className="generate-button"
                    type="submit"
                    disabled={
                      authLoading
                    }
                    style={{
                      width:
                        "100%",
                    }}
                  >
                    {authLoading
                      ? "Resetting..."
                      : "Reset Password"}
                  </button>

                </form>

                <button
                  type="button"
                  onClick={() => {
                    setAuthMode("login");
                    setAuthError("");
                    setResetSuccess("");
                  }}
                  style={{
                    display:
                      "block",

                    margin:
                      "18px auto 0",

                    border:
                      "none",

                    background:
                      "none",

                    color:
                      "#8d95ff",

                    cursor:
                      "pointer",
                  }}
                >
                  Back to sign in
                </button>

              </>

            ) : (

              <>

                <form
                  onSubmit={
                    handleAuthSubmit
                  }
                >

                  <label>
                    Email
                  </label>


                  <input
                    type="email"
                    value={
                      authEmail
                    }
                    onChange={
                      event =>
                        setAuthEmail(
                          event.target.value
                        )
                    }
                    required
                    placeholder="you@example.com"
                    style={{
                      width:
                        "100%",

                      boxSizing:
                        "border-box",

                      marginBottom:
                        "15px",
                    }}
                  />


                  <label>
                    Password
                  </label>


                  <input
                    type="password"
                    value={
                      authPassword
                    }
                    onChange={
                      event =>
                        setAuthPassword(
                          event.target.value
                        )
                    }
                    required
                    placeholder="Password"
                    style={{
                      width:
                        "100%",

                      boxSizing:
                        "border-box",

                      marginBottom:
                        "18px",
                    }}
                  />

                  {authMode === "login" && (
                    <button
                      type="button"
                      onClick={() => {
                        setAuthMode("forgot");
                        setAuthError("");
                        setResetSuccess("");
                      }}
                      style={{
                        display:
                          "block",

                        margin:
                          "0 auto 18px",

                        border:
                          "none",

                        background:
                          "none",

                        color:
                          "#8d95ff",

                        cursor:
                          "pointer",

                        fontWeight:
                          600,
                      }}
                    >
                      Forgot password?
                    </button>
                  )}



                  <button
                    className="generate-button"
                    type="submit"
                    disabled={
                      authLoading
                    }
                    style={{
                      width:
                        "100%",
                    }}
                  >
                    {authLoading
                      ? "Please wait..."
                      : authMode ===
                        "login"
                        ? "Sign In"
                        : "Create Account"}
                  </button>

                </form>


                <div
                  style={{
                    textAlign:
                      "center",

                    marginTop:
                      "20px",
                  }}
                >

                  {authMode ===
                  "login" ? (

                    <p>
                      Don't have an
                      account?{" "}

                      <button
                        type="button"
                        onClick={() =>
                          switchAuthMode(
                            "signup"
                          )
                        }
                        style={{
                          border:
                            "none",

                          background:
                            "none",

                          color:
                            "#8d95ff",

                          cursor:
                            "pointer",

                          fontWeight:
                            600,
                        }}
                      >
                        Sign up
                      </button>
                    </p>

                  ) : (

                    <p>
                      Already have an
                      account?{" "}

                      <button
                        type="button"
                        onClick={() =>
                          switchAuthMode(
                            "login"
                          )
                        }
                        style={{
                          border:
                            "none",

                          background:
                            "none",

                          color:
                            "#8d95ff",

                          cursor:
                            "pointer",

                          fontWeight:
                            600,
                        }}
                      >
                        Sign in
                      </button>
                    </p>

                  )}

                </div>

              </>

            )}

          </section>

        </main>

      </div>
    );
  }


  /* =======================================================
     WELCOME
  ======================================================= */

  if (
    page === "welcome"
  ) {

    return (
      <div className="app">

        {renderNavbar(
          "home"
        )}


        <main
          style={{
            maxWidth:
              "1000px",

            margin:
              "0 auto",

            padding:
              "60px 20px",
          }}
        >

          <section
            className="coming-card"
            style={{
              textAlign:
                "center",
            }}
          >

            <AlokoAssistant
              size={130}
            />

            <p className="eyebrow">
              WELCOME TO ALOKO
            </p>

            <h1>
              Hi, this is Aloko 
            </h1>

            <p
              style={{
                maxWidth:
                  "650px",

                margin:
                  "0 auto 30px",
              }}
            >
              Which service should I
              help you with today?
            </p>


            <div className="feature-grid">

              <button
                className="feature-card"
                onClick={() =>
                  setPage(
                    "avatar"
                  )
                }
                style={{
                  textAlign:
                    "left",

                  cursor:
                    "pointer",
                }}
              >

                <div className="feature-icon">
                  
                </div>

                <h3>
                  Create AI Video
                </h3>

                <p>
                  First create your
                  avatar, test your
                  microphone, then
                  make your Creator
                  video.
                </p>

                <span className="feature-link">
                  Start 
                </span>

              </button>


              <button
                className="feature-card"
                onClick={() =>
                  setPage(
                    "voice"
                  )
                }
                style={{
                  textAlign:
                    "left",

                  cursor:
                    "pointer",
                }}
              >

                <div className="feature-icon">
                  
                </div>

                <h3>
                  AI Voice
                </h3>

                <p>
                  Create natural speech
                  with AI voices.
                </p>

                <span className="feature-link">
                  Create voice 
                </span>

              </button>


              <button
                className="feature-card"
                onClick={() =>
                  setPage(
                    "translator"
                  )
                }
                style={{
                  textAlign:
                    "left",

                  cursor:
                    "pointer",
                }}
              >

                <div className="feature-icon">
                  
                </div>

                <h3>
                  Voice Translator
                </h3>

                <p>
                  Translate spoken voice
                  into another language.
                </p>

                <span className="feature-link">
                  Translate 
                </span>

              </button>


              <button
                className="feature-card business-card"
                type="button"
                onClick={() => setPage("business")}
                style={{ textAlign: "left", cursor: "pointer" }}
              >

                <div className="feature-icon">
                  ðŸ¢
                </div>

                <h3>
                  Business AI Video
                </h3>

                <p>
                  A separate advanced
                  workspace for companies,
                  brands, products,
                  teams and multiple
                  assets.
                </p>

                <span className="feature-link">
                  Open Business AI 
                </span>

              </button>

            </div>

          </section>

        </main>

      </div>
    );
  }


  /* =======================================================
     AVATAR CREATION
  ======================================================= */

  if (
    page === "avatar"
  ) {

    return (
      <div className="app">

        {renderNavbar(
          "avatar"
        )}


        <main
          style={{
            maxWidth:
              "1000px",

            margin:
              "0 auto",

            padding:
              "50px 20px",
          }}
        >

          <div
            style={{
              display:
                "flex",

              gap:
                "20px",

              alignItems:
                "center",

              marginBottom:
                "35px",

              flexWrap:
                "wrap",
            }}
          >

            <AlokoAssistant />

            <div>

              <p className="eyebrow">
                STEP 1  -  AVATAR
              </p>

              <h1>
                Let's create your avatar
              </h1>

              <p>
                Choose an Image Avatar
                or the upcoming Video
                Avatar system.
              </p>

            </div>

          </div>


          {error && (
            <div className="error">
              {error}
            </div>
          )}


          <div
            className="feature-grid"
            style={{
              gridTemplateColumns:
                "repeat(2, minmax(0, 1fr))",
            }}
          >

            <button
              type="button"
              className="feature-card"
              onClick={() =>
                setAvatarType(
                  "image"
                )
              }
              style={{
                textAlign:
                  "left",

                cursor:
                  "pointer",

                border:
                  avatarType ===
                  "image"
                    ? "2px solid #8d95ff"
                    : undefined,
              }}
            >

              <div className="feature-icon">
                
              </div>

              <h3>
                Image Avatar
              </h3>

              <p>
                Upload a clear photo
                for talking-avatar
                video generation.
              </p>

              <strong>
                Available now
              </strong>

            </button>


            <button
              type="button"
              className="feature-card"
              onClick={() =>
                setAvatarType(
                  "video"
                )
              }
              style={{
                textAlign:
                  "left",

                cursor:
                  "pointer",

                border:
                  avatarType ===
                  "video"
                    ? "2px solid #8d95ff"
                    : undefined,
              }}
            >

              <div className="feature-icon">
                
              </div>

              <h3>
                Video Avatar
              </h3>

              <p>
                A more advanced avatar
                pipeline for future
                natural movement and
                scene interaction.
              </p>

              <strong>
                Coming next
              </strong>

            </button>

          </div>


          {avatarType ===
            "image" && (

            <section
              className="coming-card"
              style={{
                marginTop:
                  "30px",

                textAlign:
                  "left",
              }}
            >

              <h2>
                Create your Image Avatar
              </h2>

              <p>
                Use a clear, well-lit
                photograph where the
                face is easy to see.
              </p>


              <label>
                Avatar name
              </label>


              <input
                value={
                  avatarName
                }
                onChange={
                  event =>
                    setAvatarName(
                      event.target.value
                    )
                }
                placeholder="My Avatar"
              />


              <label
                style={{
                  display:
                    "block",

                  marginTop:
                    "18px",
                }}
              >
                Choose photo
              </label>


              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={
                  event =>
                    setAvatarImage(
                      event.target.files?.[0] ||
                      null
                    )
                }
              />


              {avatarImage && (
                <p
                  style={{
                    marginTop:
                      "10px",
                  }}
                >
                  Selected:
                  {" "}
                  {avatarImage.name}
                </p>
              )}


              <button
                className="generate-button"
                disabled={
                  avatarUploading ||
                  !avatarImage
                }
                onClick={
                  handleCreateAvatar
                }
                style={{
                  marginTop:
                    "20px",
                }}
              >
                {avatarUploading
                  ? "Creating avatar..."
                  : "Create My Avatar"}
              </button>

            </section>
          )}


          {avatarType ===
            "video" && (

            <div
              className="error"
              style={{
                marginTop:
                  "25px",
              }}
            >
              Video Avatar has its own
              processing pipeline and
              will be added separately
              from Image Avatar.
            </div>

          )}

        </main>

      </div>
    );
  }


  /* =======================================================
     VOICE TEST
  ======================================================= */

  if (
    page === "voice-test"
  ) {

    return (
      <div className="app">

        {renderNavbar(
          "avatar"
        )}


        <main
          style={{
            maxWidth:
              "900px",

            margin:
              "0 auto",

            padding:
              "50px 20px",
          }}
        >

          <section className="coming-card">

            <div
              style={{
                display:
                  "flex",

                alignItems:
                  "center",

                gap:
                  "20px",

                flexWrap:
                  "wrap",
              }}
            >

              <AlokoAssistant />

              <div>

                <p className="eyebrow">
                  STEP 2  -  PERSONAL VOICE
                </p>

                <h1>
                  Create your personal voice
                </h1>

                <p>
                  Record one clear voice sample. Aloko will save it to your account so it can become your personal voice when voice cloning is connected.
                </p>

              </div>

            </div>


            {error && (
              <div className="error">
                {error}
              </div>
            )}


            <div
              style={{
                marginTop:
                  "30px",

                padding:
                  "20px",

                borderRadius:
                  "14px",

                background:
                  "rgba(141,149,255,0.08)",
              }}
            >

              <strong>
                Read this:
              </strong>

              <p>
                â€œHello, this is my voice
                on Aloko. I am testing my
                microphone before creating
                my AI video.â€
              </p>

            </div>


            <div style={{ marginTop: "20px" }}>
              <label>Personal voice name</label>
              <input
                value={personalVoiceName}
                onChange={event => setPersonalVoiceName(event.target.value)}
                placeholder="My Personal Voice"
                maxLength={100}
                style={{ width: "100%", marginTop: "8px" }}
              />
            </div>


            {!voiceRecording ? (

              <button
                className="generate-button"
                onClick={
                  startVoiceTest
                }
                style={{
                  marginTop:
                    "22px",
                }}
              >
                ðŸŽ™ Start Voice Recording
              </button>

            ) : (

              <button
                className="generate-button"
                onClick={
                  stopVoiceTest
                }
                style={{
                  marginTop:
                    "22px",
                }}
              >
                â¹ Stop Recording{" "}
                {voiceRecordingSeconds}s
              </button>

            )}


            {personalVoiceRecordingBlob && !voiceRecording && (
              <button
                className="generate-button"
                onClick={saveRecordedPersonalVoice}
                disabled={personalVoiceUploading}
                style={{ marginTop: "22px" }}
              >
                {personalVoiceUploading ? "Saving personal voice..." : " Save My Personal Voice"}
              </button>
            )}


            {voiceTestAudioUrl && (

              <div
                style={{
                  marginTop:
                    "25px",
                }}
              >

                <p>
                  Your recorded sample:
                </p>

                <audio
                  controls
                  src={
                    voiceTestAudioUrl
                  }
                  style={{
                    width:
                      "100%",
                  }}
                />

              </div>

            )}


            <div
              style={{
                marginTop:
                  "25px",

                padding:
                  "15px",

                borderRadius:
                  "12px",

                background:
                  "rgba(45,106,79,0.12)",
              }}
            >

              <strong>
                Next step
              </strong>

              <p>
                Your recording is stored securely in your Aloko voice library. Phase 6 will connect the voice-cloning provider so this recording can generate new speech in your voice.
              </p>

            </div>


            <button
              className="generate-button"
              onClick={() =>
                setPage(
                  "video"
                )
              }
              style={{
                marginTop:
                  "20px",
              }}
            >
              Continue to Creator Video 
            </button>

          </section>

        </main>

      </div>
    );
  }


  /* =======================================================
     HOME
  ======================================================= */

  if (
    page === "home"
  ) {

    return (
      <div className="app">

        {renderNavbar(
          "home"
        )}


        <main className="hero">

          <section
            style={{
              display:
                "flex",

              justifyContent:
                "center",

              alignItems:
                "center",

              gap:
                "20px",

              flexWrap:
                "wrap",

              marginBottom:
                "25px",
            }}
          >

            <AlokoAssistant />

            <div>

              <p className="eyebrow">
                ALOKO AI ASSISTANT
              </p>

              <h2
                style={{
                  margin:
                    0,
                }}
              >
                Hi, this is Aloko 
              </h2>

              <p>
                Which service should I
                help you with?
              </p>

            </div>

          </section>


          <p className="eyebrow">
            AI CREATION PLATFORM
          </p>


          <h1>
            Create with AI.
            <br />
            <span>
              Make it yours.
            </span>
          </h1>


          <p className="hero-description">
            Generate voices, translate
            speech and create AI videos
            from one powerful platform.
          </p>


          <section
            className="home-section"
            style={{
              marginTop: "30px",
            }}
          >
            <div
              style={{
                padding: "28px",
                borderRadius: "24px",
                border: "1px solid rgba(141,149,255,.25)",
                background: "linear-gradient(135deg, rgba(141,149,255,.12), rgba(255,255,255,.035))",
                boxShadow: "0 20px 60px rgba(0,0,0,.16)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "18px",
                  marginBottom: "20px",
                  flexWrap: "wrap",
                }}
              >
                <AlokoAssistant size={78} />
                <div style={{ flex: 1, minWidth: "240px" }}>
                  <p className="eyebrow" style={{ marginBottom: "6px" }}>
                    ALOKO AI DIRECTOR
                  </p>
                  <h2 style={{ margin: 0 }}>
                    Create an entire video from one idea
                  </h2>
                  <p style={{ marginBottom: 0 }}>
                    Describe your idea and Aloko will write the script,
                    break it into scenes, select available voices and
                    avatars, and create an editable Creator Studio project.
                  </p>
                </div>
              </div>

              <textarea
                value={aiDirectorIdea}
                onChange={event => setAiDirectorIdea(event.target.value)}
                rows={5}
                maxLength={10000}
                disabled={aiDirectorLoading}
                placeholder="Example: Create a motivational 60-second video explaining why young Africans should learn AI and use it to solve real problems."
                style={{
                  width: "100%",
                  resize: "vertical",
                  marginBottom: "18px",
                }}
              />

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                  gap: "16px",
                  marginBottom: "18px",
                }}
              >
                <div
                  style={{
                    padding: "18px",
                    borderRadius: "18px",
                    background: "rgba(255,255,255,.035)",
                    border: "1px solid rgba(255,255,255,.08)",
                  }}
                >
                  <div style={{ marginBottom: "10px" }}>
                    <strong> Voice for this video</strong>
                    <p style={{ margin: "5px 0 0", fontSize: "12px", opacity: .65 }}>
                      Choose who should speak. You can still change voices scene by scene later.
                    </p>
                  </div>

                  <select
                    value={aiDirectorVoiceMode}
                    onChange={event => setAiDirectorVoiceMode(event.target.value)}
                    disabled={aiDirectorLoading}
                    style={{ width: "100%" }}
                  >
                    <option value="auto"> Let Aloko Choose</option>
                    <option value="personal">
                       My Personal Voice
                    </option>
                    <option value="builtin"> Choose an Aloko Voice</option>
                    <option value="none">â­ï¸ No Voice Yet - Add Later</option>
                  </select>

                  {aiDirectorVoiceMode === "personal" && (
                    <select
                      value={aiDirectorPersonalVoice}
                      onChange={event => setAiDirectorPersonalVoice(event.target.value)}
                      disabled={aiDirectorLoading}
                      style={{ width: "100%", marginTop: "10px" }}
                    >
                      <option value="">Select your personal voice</option>
                      {creatorMyVoices
                        .filter(v => v.voice_type === "custom" && v.status === "ready" && v.provider_voice_id)
                        .map(voice => (
                          <option key={voice.id} value={voice.id}>
                            {voice.name || `Personal Voice ${voice.id}`}
                          </option>
                        ))}
                    </select>
                  )}

                  {aiDirectorVoiceMode === "builtin" && (
                    <select
                      value={aiDirectorBuiltinVoice}
                      onChange={event => setAiDirectorBuiltinVoice(event.target.value)}
                      disabled={aiDirectorLoading || !voices.length}
                      style={{ width: "100%", marginTop: "10px" }}
                    >
                      <option value="">Select an Aloko voice</option>
                      {voices.map(voice => (
                        <option key={voice.tts_voice} value={voice.tts_voice}>
                          {voice.name || voice.tts_voice}
                          {voice.language ? `  -  ${getLanguageName(voice.language)}` : ""}
                        </option>
                      ))}
                    </select>
                  )}

                  {aiDirectorVoiceMode === "personal" && !creatorMyVoices.some(v => v.voice_type === "custom" && v.status === "ready" && v.provider_voice_id) && (
                    <div style={{ marginTop: "10px" }}>
                      <p style={{ margin: "0 0 10px", fontSize: "12px", opacity: .72 }}>
                        You don't have a ready personal voice yet. Record one and save it to your Aloko voice library.
                      </p>
                      <button
                        type="button"
                        onClick={() => setPage("voice-test")}
                        disabled={aiDirectorLoading}
                        style={{ padding: "10px 14px", borderRadius: "10px", border: "1px solid rgba(141,149,255,.45)", background: "rgba(141,149,255,.10)", color: "inherit", cursor: "pointer" }}
                      >
                        ðŸŽ™ Record personal voice
                      </button>
                    </div>
                  )}
                </div>

                <div
                  style={{
                    padding: "18px",
                    borderRadius: "18px",
                    background: "rgba(255,255,255,.035)",
                    border: "1px solid rgba(255,255,255,.08)",
                  }}
                >
                  <div style={{ marginBottom: "10px" }}>
                    <strong> Avatar for this video</strong>
                    <p style={{ margin: "5px 0 0", fontSize: "12px", opacity: .65 }}>
                      Choose an avatar now or let Aloko decide from your available avatars.
                    </p>
                  </div>

                  <select
                    value={aiDirectorAvatarMode}
                    onChange={event => setAiDirectorAvatarMode(event.target.value)}
                    disabled={aiDirectorLoading}
                    style={{ width: "100%" }}
                  >
                    <option value="auto"> Let Aloko Choose</option>
                    <option value="selected" disabled={!avatars.length}> Choose My Avatar</option>
                    <option value="none">â­ï¸ No Avatar Yet - Add Later</option>
                  </select>

                  {aiDirectorAvatarMode === "selected" && (
                    <select
                      value={aiDirectorAvatarId}
                      onChange={event => setAiDirectorAvatarId(event.target.value)}
                      disabled={aiDirectorLoading || !avatars.length}
                      style={{ width: "100%", marginTop: "10px" }}
                    >
                      <option value="">Select an avatar</option>
                      {avatars.map(avatar => (
                        <option key={avatar.id} value={avatar.id}>
                          {avatar.name || `Avatar ${avatar.id}`}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "12px",
                  flexWrap: "wrap",
                }}
              >
                <span style={{ fontSize: "12px", opacity: .6 }}>
                  {aiDirectorIdea.length}/10000
                </span>

                <button
                  type="button"
                  className="generate-button"
                  onClick={handleAIDirectorGenerate}
                  disabled={
                    aiDirectorLoading ||
                    !aiDirectorIdea.trim() ||
                    (aiDirectorVoiceMode === "personal" && !aiDirectorPersonalVoice) ||
                    (aiDirectorVoiceMode === "builtin" && !aiDirectorBuiltinVoice) ||
                    (aiDirectorAvatarMode === "selected" && !aiDirectorAvatarId)
                  }
                >
                  {aiDirectorLoading
                    ? "Aloko is creating your project..."
                    : " Create with AI Director"}
                </button>
              </div>

              {aiDirectorLoading && (
                <div
                  style={{
                    marginTop: "16px",
                    padding: "14px 16px",
                    borderRadius: "14px",
                    background: "rgba(255,255,255,.04)",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    fontSize: "13px",
                    opacity: .85,
                  }}
                >
                  <div className="spinner" style={{ width: "18px", height: "18px" }} />
                  Understanding idea  Writing script  Planning scenes  Building project
                </div>
              )}

              {aiDirectorError && (
                <div className="error" style={{ marginTop: "14px" }}>
                  {aiDirectorError}
                </div>
              )}

              {aiDirectorResult?.project && !aiDirectorLoading && (
                <div
                  style={{
                    marginTop: "14px",
                    padding: "14px 16px",
                    borderRadius: "14px",
                    background: "rgba(72,200,130,.08)",
                    border: "1px solid rgba(72,200,130,.2)",
                  }}
                >
                  <strong>{aiDirectorResult.project.name}</strong>
                  <span style={{ marginLeft: "10px", opacity: .7, fontSize: "13px" }}>
                    {aiDirectorResult.scenes?.length || 0} scenes created
                  </span>
                </div>
              )}
            </div>
          </section>


          {error && (
            <div className="error">
              {error}
            </div>
          )}


          <section className="home-section">

            <div className="section-heading">

              <h2>
                Creator
              </h2>

              <p>
                Tools for individual
                creators.
              </p>

            </div>


            <div className="feature-grid">

              <div
                className="feature-card clickable"
                onClick={() =>
                  setPage(
                    "voice"
                  )
                }
              >

                <div className="feature-icon">
                  
                </div>

                <h3>
                  AI Voice
                </h3>

                <p>
                  Turn text into natural
                  speech with AI voices,
                  languages and accents.
                </p>

                <span className="feature-link">
                  Create voice 
                </span>

              </div>


              <div
                className="feature-card clickable"
                onClick={() =>
                  setPage(
                    "translator"
                  )
                }
              >

                <div className="feature-icon">
                  
                </div>

                <h3>
                  Voice Translator
                </h3>

                <p>
                  Translate spoken audio
                  into another language
                  and generate a new voice.
                </p>

                <span className="feature-link">
                  Translate voice 
                </span>

              </div>


              <div
                className="feature-card clickable"
                onClick={() =>
                  setPage(
                    avatars.length
                      ? "video"
                      : "avatar"
                  )
                }
              >

                <div className="feature-icon">
                  
                </div>

                <h3>
                  Creator AI Video
                </h3>

                <p>
                  Create your avatar,
                  test your microphone and
                  produce talking-avatar
                  videos.
                </p>

                <span className="feature-link">
                  Create video 
                </span>

              </div>


              <div className="feature-card">

                <div className="feature-icon">
                  
                </div>

                <h3>
                  AI Photo
                </h3>

                <p>
                  Create and transform
                  images with AI.
                </p>

                <span className="feature-link">
                  Coming soon 
                </span>

              </div>

            </div>

          </section>


          <section className="home-section">

            <div className="section-heading">

              <h2>
                Business
              </h2>

              <p>
                A separate advanced
                product for companies.
              </p>

            </div>


            <div className="feature-grid">

              <button
                className="feature-card business-card"
                type="button"
                onClick={() => setPage("business")}
                style={{ textAlign: "left", cursor: "pointer" }}
              >

                <div className="feature-icon">
                  ðŸ¢
                </div>

                <h3>
                  Business AI Video
                </h3>

                <p>
                  A completely separate
                  business workspace with
                  company profiles, brand
                  kits, products, multiple
                  images, multiple videos,
                  multiple avatars, scenes,
                  AI scripts, marketing,
                  sales, training and
                  team features.
                </p>

                <span className="feature-link">
                  Open Business AI 
                </span>

              </button>

            </div>

          </section>


          <section className="home-section">

            <div className="section-heading">

              <h2>
                AI Intelligence
              </h2>

              <p>
                Turn documents and media
                into structured knowledge.
              </p>

            </div>


            <div className="feature-grid">

              <div className="feature-card">

                <div className="feature-icon">
                  
                </div>

                <h3>
                  AI Extract
                </h3>

                <p>
                  Extract text, tables,
                  images, video frames and
                  transcripts.
                </p>

                <span className="feature-link">
                  Coming soon 
                </span>

              </div>


              <div className="feature-card">

                <div className="feature-icon">
                  ðŸ§ 
                </div>

                <h3>
                  AI Knowledge
                </h3>

                <p>
                  Build an intelligent
                  knowledge base from your
                  documents and information.
                </p>

                <span className="feature-link">
                  Coming soon 
                </span>

              </div>


              <div className="feature-card clickable" onClick={() => setPage("university-student")} style={{cursor:"pointer"}}><div className="feature-icon"></div><h3>Student Dashboard</h3><p>View courses, results, GPA, attendance, clearance and payments.</p><span className="feature-link">Open Student Dashboard </span></div>

              <div className="feature-card clickable" onClick={openIndependentLecturer} style={{cursor:"pointer"}}>

                <div className="feature-icon">
                  
                </div>

                <h3>
                  Independent Lecturer
                </h3>

                <p>
                  Academic intelligence for universities,
                  lecturers and students.
                </p>

                <span className="feature-link">
                  Open Independent Lecturer 
                </span>

              </div>

            </div>

          </section>

        </main>

      </div>
    );
  }


  /* =======================================================
     AI VOICE PAGE
  ======================================================= */

  if (
    page === "voice"
  ) {

    return (
      <div className="app">

        {renderNavbar(
          "voice"
        )}


        <main className="voice-page">

          <button
            className="back-button clickable"
            onClick={() =>
              setPage(
                "home"
              )
            }
          >
             Back
          </button>


          <div className="voice-page-header">

            <p className="eyebrow">
              AI VOICE
            </p>

            <h1>
              Create your voice
            </h1>

            <p>
              Turn your script into
              natural-sounding speech.
            </p>

          </div>


          {error && (
            <div className="error">
              {error}
            </div>
          )}


          {loadingVoices ? (

            <div className="loading">
              Loading voices...
            </div>

          ) : (

            <div className="voice-page-layout">

              <section className="voice-builder">

                <div className="voice-title">

                  <h3>
                    Voice settings
                  </h3>

                  <p>
                    Choose language, country,
                    accent, gender and style.
                  </p>

                </div>


                <div className="voice-filters">

                  <div className="filter-group">

                    <label>
                      Language
                    </label>

                    <select
                      value={
                        selectedLanguage
                      }
                      onChange={
                        event =>
                          handleLanguageChange(
                            event.target.value
                          )
                      }
                    >

                      {languages.map(
                        language => (

                          <option
                            key={
                              language
                            }
                            value={
                              language
                            }
                          >
                            {getLanguageName(
                              language
                            )}
                          </option>

                        )
                      )}

                    </select>

                  </div>


                  <div className="filter-group">

                    <label>
                      Country
                    </label>

                    <select
                      value={
                        selectedCountry
                      }
                      onChange={
                        event =>
                          handleCountryChange(
                            event.target.value
                          )
                      }
                    >

                      <option value="">
                        All countries
                      </option>

                      {countries.map(
                        country => (

                          <option
                            key={
                              country
                            }
                            value={
                              country
                            }
                          >
                            {getCountryName(
                              country
                            )}
                          </option>

                        )
                      )}

                    </select>

                  </div>

                </div>


                <div className="gender-filter">

                  <label>
                    Gender
                  </label>

                  <div className="gender-buttons">

                    {[
                      ["", "All"],
                      [
                        "female",
                        "Female",
                      ],
                      [
                        "male",
                        "Male",
                      ],
                    ].map(
                      ([value, label]) => (

                        <button
                          type="button"
                          key={
                            value ||
                            "all"
                          }
                          className={
                            selectedGender ===
                            value
                              ? "active"
                              : ""
                          }
                          onClick={() =>
                            setSelectedGender(
                              value
                            )
                          }
                        >
                          {label}
                        </button>

                      )
                    )}

                  </div>

                </div>


                <div className="voice-select">

                  <label>
                    Accent
                  </label>

                  <select
                    value={
                      selectedAccent
                    }
                    onChange={
                      event =>
                        setSelectedAccent(
                          event.target.value
                        )
                    }
                  >

                    <option value="">
                      All accents
                    </option>

                    {accents.map(
                      accent => (

                        <option
                          key={
                            accent
                          }
                          value={
                            accent
                          }
                        >
                          {getAccentName(
                            accent
                          )}
                        </option>

                      )
                    )}

                  </select>

                </div>


                <div className="voice-select">

                  <label>
                    Style
                  </label>

                  <select
                    value={
                      selectedStyle
                    }
                    onChange={
                      event =>
                        setSelectedStyle(
                          event.target.value
                        )
                    }
                  >

                    <option value="">
                      All styles
                    </option>

                    {STYLE_OPTIONS.map(
                      style => (

                        <option
                          key={
                            style
                          }
                          value={
                            style
                          }
                        >
                          {style}
                        </option>

                      )
                    )}

                  </select>

                </div>


                <div className="voice-select">

                  <label>
                    Voice
                  </label>

                  <select
                    value={
                      selectedVoice
                    }
                    onChange={
                      event =>
                        setSelectedVoice(
                          event.target.value
                        )
                    }
                  >

                    {filteredVoices.map(
                      voice => (

                        <option
                          key={
                            voice.tts_voice
                          }
                          value={
                            voice.tts_voice
                          }
                        >
                          {voice.name ||
                            voice.tts_voice}
                        </option>

                      )
                    )}

                  </select>

                </div>


                <button
                  className="voice-preview-button"
                  onClick={
                    handlePreviewVoice
                  }
                  disabled={
                    previewingVoice ||
                    !selectedVoice
                  }
                >
                  {previewingVoice
                    ? "Generating preview..."
                    : " Preview Voice"}
                </button>


                {previewAudioUrl && (

                  <audio
                    controls
                    autoPlay
                    src={
                      previewAudioUrl
                    }
                    style={{
                      width:
                        "100%",

                      marginTop:
                        "15px",
                    }}
                  />

                )}

              </section>


              <section className="voice-script-panel">

                <div className="voice-script-header">

                  <div>

                    <h3>
                      Your script
                    </h3>

                    <p>
                      Enter the text you
                      want your AI voice
                      to speak.
                    </p>

                  </div>

                  <span>
                    {script.length}
                    {" / 5000"}
                  </span>

                </div>


                <textarea
                  value={
                    script
                  }
                  onChange={
                    event =>
                      setScript(
                        event.target.value
                      )
                  }
                  maxLength={
                    5000
                  }
                  placeholder="Welcome to Aloko, your AI creation platform..."
                />


                <button
                  className="generate-button"
                  disabled={
                    generating ||
                    !script.trim() ||
                    !selectedVoice
                  }
                  onClick={
                    handleGenerateVoice
                  }
                >
                  {generating
                    ? "Generating voice..."
                    : "Generate Voice"}
                </button>


                {result?.audio_url && (

                  <div className="audio-result">

                    <span className="result-label">
                      GENERATED VOICE
                    </span>

                    <h3>
                      {result.voice_name ||
                        "Generated voice"}
                    </h3>

                    <audio
                      controls
                      src={
                        `${API_BASE_URL}${result.audio_url}`
                      }
                    />

                    <div className="result-actions">

                      <a
                        href={
                          `${API_BASE_URL}${result.audio_url}`
                        }
                        download
                      >
                        Download MP3
                      </a>

                    </div>

                  </div>

                )}

              </section>

            </div>

          )}

        </main>

      </div>
    );
  }


  /* =======================================================
     TRANSLATOR PAGE
  ======================================================= */

  if (
    page === "translator"
  ) {

    return (
      <div className="app">

        {renderNavbar(
          "translator"
        )}


        <main className="translator-page">

          <button
            className="back-button clickable"
            onClick={() =>
              setPage(
                "home"
              )
            }
          >
             Back
          </button>


          <div className="translator-header">

            <p className="eyebrow">
              VOICE TRANSLATOR
            </p>

            <h1>
              Translate your voice
            </h1>

            <p>
              Record or upload audio,
              choose a target language
              and generate translated
              speech.
            </p>

          </div>


          {translatorError && (
            <div className="error">
              {translatorError}
            </div>
          )}


          <div className="translator-layout">

            <section className="translator-input-panel">

              <div className="translator-section">

                <h3>
                  1. Your voice
                </h3>

                <div className="translator-record-box">

                  {!recording ? (

                    <button
                      className="translator-record-button"
                      onClick={
                        startTranslatorRecording
                      }
                    >
                      ðŸŽ™ Start Recording
                    </button>

                  ) : (

                    <button
                      className="translator-record-button recording"
                      onClick={
                        stopTranslatorRecording
                      }
                    >
                      â¹ Stop Recording{" "}
                      {recordingSeconds}s
                    </button>

                  )}


                  <span>
                    or
                  </span>


                  <label className="translator-upload-button">

                    ðŸ“ Upload Audio

                    <input
                      type="file"
                      accept="audio/*"
                      onChange={
                        event =>
                          setTranslatorFile(
                            event.target.files?.[0] ||
                            null
                          )
                      }
                    />

                  </label>

                </div>


                {translatorFile && (

                  <div className="translator-file">

                    <strong>
                      {translatorFile.name}
                    </strong>

                    <span>
                      {(
                        translatorFile.size /
                        1024 /
                        1024
                      ).toFixed(2)}
                      {" "}
                      MB
                    </span>

                  </div>

                )}

              </div>


              <div className="translator-section">

                <h3>
                  2. Target language
                </h3>

                <select
                  value={
                    translatorTargetLanguage
                  }
                  onChange={
                    event => {

                      setTranslatorTargetLanguage(
                        event.target.value
                      );

                      setTranslatorCountry("");
                      setTranslatorAccent("");
                      setTranslatorGender("");
                      setTranslatorVoice("");

                      clearTranslatorPreview();
                    }
                  }
                >

                  {translatorLanguages.map(
                    language => (

                      <option
                        key={
                          language.code
                        }
                        value={
                          language.code
                        }
                      >
                        {language.name}
                      </option>

                    )
                  )}

                </select>

              </div>


              <div className="translator-section">

                <h3>
                  3. Country
                </h3>

                <select
                  value={
                    translatorCountry
                  }
                  onChange={
                    event => {

                      setTranslatorCountry(
                        event.target.value
                      );

                      setTranslatorAccent("");
                      setTranslatorGender("");
                      setTranslatorVoice("");

                      clearTranslatorPreview();
                    }
                  }
                >

                  <option value="">
                    All countries
                  </option>

                  {translatorCountries.map(
                    country => (

                      <option
                        key={
                          country
                        }
                        value={
                          country
                        }
                      >
                        {getCountryName(
                          country
                        )}
                      </option>

                    )
                  )}

                </select>

              </div>


              <div className="translator-section">

                <h3>
                  4. Accent
                </h3>

                <select
                  value={
                    translatorAccent
                  }
                  onChange={
                    event => {

                      setTranslatorAccent(
                        event.target.value
                      );

                      setTranslatorGender("");
                      setTranslatorVoice("");

                      clearTranslatorPreview();
                    }
                  }
                >

                  <option value="">
                    All accents
                  </option>

                  {translatorAccents.map(
                    accent => (

                      <option
                        key={
                          accent
                        }
                        value={
                          accent
                        }
                      >
                        {getAccentName(
                          accent
                        )}
                      </option>

                    )
                  )}

                </select>

              </div>


              <div className="translator-section">

                <h3>
                  5. Voice
                </h3>


                <div className="gender-buttons">

                  {[
                    ["", "All"],
                    [
                      "female",
                      "Female",
                    ],
                    [
                      "male",
                      "Male",
                    ],
                  ].map(
                    ([value, label]) => (

                      <button
                        type="button"
                        key={
                          value ||
                          "all"
                        }
                        className={
                          translatorGender ===
                          value
                            ? "active"
                            : ""
                        }
                        onClick={() =>
                          setTranslatorGender(
                            value
                          )
                        }
                      >
                        {label}
                      </button>

                    )
                  )}

                </div>


                <select
                  value={
                    translatorVoice
                  }
                  onChange={
                    event =>
                      setTranslatorVoice(
                        event.target.value
                      )
                  }
                >

                  {translatorVoices.map(
                    voice => (

                      <option
                        key={
                          voice.tts_voice
                        }
                        value={
                          voice.tts_voice
                        }
                      >
                        {voice.name ||
                          voice.tts_voice}
                      </option>

                    )
                  )}

                </select>


                <button
                  type="button"
                  className="voice-preview-button"
                  onClick={
                    handleTranslatorPreview
                  }
                  disabled={
                    translatorPreviewLoading ||
                    !translatorVoice
                  }
                >
                  {translatorPreviewLoading
                    ? "Generating..."
                    : " Preview Voice"}
                </button>


                {translatorPreviewAudioUrl && (

                  <audio
                    controls
                    src={
                      translatorPreviewAudioUrl
                    }
                    style={{
                      width:
                        "100%",

                      marginTop:
                        "12px",
                    }}
                  />

                )}

              </div>


              <button
                className="generate-button translator-generate-button"
                disabled={
                  translatorLoading ||
                  !translatorFile ||
                  !translatorVoice
                }
                onClick={
                  handleTranslateVoice
                }
              >
                {translatorLoading
                  ? "Translating..."
                  : " Translate Voice"}
              </button>

            </section>


            <section className="translator-result-panel">

              {translatorLoading ? (

                <div className="preview-empty">

                  <div className="spinner"></div>

                  <h2>
                    Translating your voice
                  </h2>

                  <p>
                    Aloko is transcribing,
                    translating and generating
                    your new voice.
                  </p>

                </div>

              ) : translatorResult ? (

                <div className="translator-result">

                  <span className="result-label">
                    TRANSLATED VOICE
                  </span>

                  <h2>
                    Your translation is ready
                  </h2>


                  <div className="translator-text-card">

                    <div>

                      <span>
                        ORIGINAL
                      </span>

                      <p>
                        {
                          translatorResult.source_text
                        }
                      </p>

                    </div>


                    <div>

                      <span>
                        TRANSLATION
                      </span>

                      <p>
                        {
                          translatorResult.translated_text
                        }
                      </p>

                    </div>

                  </div>


                  <audio
                    controls
                    src={
                      `${API_BASE_URL}${translatorResult.audio_url}`
                    }
                  />


                  <div className="result-actions">

                    <a
                      href={
                        `${API_BASE_URL}${translatorResult.audio_url}`
                      }
                      download
                    >
                      Download MP3
                    </a>

                  </div>

                </div>

              ) : (

                <div className="preview-empty">

                  <div className="preview-icon">
                    
                  </div>

                  <h2>
                    Your translated voice
                    will appear here
                  </h2>

                  <p>
                    Record or upload audio,
                    choose a language and
                    generate the translation.
                  </p>

                </div>

              )}

            </section>

          </div>

        </main>

      </div>
    );
  }


  /* =======================================================
     CREATOR STUDIO
  ======================================================= */

  if (page === "video") {
    const readyPersonalVoices = creatorMyVoices.filter(v => v.voice_type === "custom" && v.status === "ready" && v.provider_voice_id);
    const selectedAvatar = avatars.find(a => Number(a.id) === Number(selectedAvatarId));

    return (
      <div className="app">
        {renderNavbar("video")}
        <main style={{ maxWidth: "1250px", margin: "0 auto", padding: "35px 20px 70px" }}>
          <button className="back-button clickable" onClick={() => setPage("home")}> Back</button>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: "20px", flexWrap: "wrap", marginBottom: "30px" }}>
            <div>
              <p className="eyebrow">ALOKO CREATOR STUDIO</p>
              <h1>Create your AI video</h1>
              <p>Build your video scene by scene, choose your avatar and voice, then render the complete MP4.</p>
            </div>
            <button className="generate-button" onClick={createNewCreatorProject} disabled={creatorSaving || creatorLoading}>+ New Project</button>
          </div>

          {error && <div className="error">{error}</div>}

          {creatorLoading ? (
            <section className="coming-card" style={{ textAlign: "center", padding: "60px 25px" }}>
              <div className="spinner"></div>
              <h2>Opening Creator Studio...</h2>
              <p>Loading your projects and scenes.</p>
            </section>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.4fr) minmax(320px, 0.8fr)", gap: "25px", alignItems: "start" }}>
              <section className="creator-panel" style={{ padding: "25px" }}>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "15px", marginBottom: "25px", flexWrap: "wrap" }}>
                  <div>
                    <span className="result-label">PROJECT</span>
                    <h2 style={{ margin: "5px 0 0" }}>{creatorProject?.name || "My AI Video"}</h2>
                  </div>
                  {creatorProjects.length > 1 && (
                    <select value={creatorProject?.id || ""} onChange={e => loadCreatorProject(Number(e.target.value))}>
                      {creatorProjects.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}
                    </select>
                  )}
                </div>

                <div className="form-section">
                  <label>Avatar</label>
                  {avatars.length === 0 ? (
                    <div className="avatar-box" style={{ padding: "20px" }}>
                      <strong>Create an avatar first.</strong>
                      <p>Your avatar will be used for the talking-video scenes.</p>
                      <button className="generate-button" onClick={() => setPage("avatar")}>Create Avatar</button>
                    </div>
                  ) : (
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: "12px" }}>
                      {avatars.map(avatar => (
                        <button key={avatar.id} type="button" onClick={() => setSelectedAvatarId(avatar.id)} style={{ border: Number(selectedAvatarId) === Number(avatar.id) ? "2px solid #8d95ff" : "1px solid rgba(255,255,255,0.12)", borderRadius: "14px", padding: "8px", background: "transparent", cursor: "pointer", textAlign: "left" }}>
                          <img src={getAvatarImageUrl(avatar.image_url)} alt={avatar.name || "Avatar"} style={{ width: "100%", aspectRatio: "1 / 1", objectFit: "cover", borderRadius: "10px", display: "block" }} />
                          <strong style={{ display: "block", marginTop: "8px" }}>{avatar.name || "My Avatar"}</strong>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="form-section" style={{ marginTop: "28px" }}>
                  <label>Voice</label>
                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <button type="button" onClick={() => setCreatorVoiceType("built_in")} style={{ padding: "10px 15px", borderRadius: "10px", border: creatorVoiceType === "built_in" ? "2px solid #8d95ff" : "1px solid rgba(255,255,255,0.12)", background: "transparent", cursor: "pointer" }}>Built-in Voice</button>
                    <button type="button" onClick={() => setCreatorVoiceType("personal")} disabled={!readyPersonalVoices.length} style={{ padding: "10px 15px", borderRadius: "10px", border: creatorVoiceType === "personal" ? "2px solid #8d95ff" : "1px solid rgba(255,255,255,0.12)", background: "transparent", cursor: readyPersonalVoices.length ? "pointer" : "not-allowed", opacity: readyPersonalVoices.length ? 1 : 0.5 }}>My Personal Voice</button>
                  </div>
                  {creatorVoiceType === "built_in" && <p style={{ marginTop: "12px" }}>The current Creator renderer uses its configured built-in voice when a personal voice is not selected.</p>}
                  {creatorVoiceType === "personal" && (readyPersonalVoices.length ? (
                    <select value={creatorSelectedPersonalVoice} onChange={e => setCreatorSelectedPersonalVoice(e.target.value)} style={{ width: "100%", marginTop: "12px" }}>
                      <option value="">Select your personal voice</option>
                      {readyPersonalVoices.map(v => <option key={v.id} value={v.id}>{v.name || "Personal Voice"}</option>)}
                    </select>
                  ) : <div style={{ marginTop: "12px", padding: "14px", borderRadius: "10px" }}>No ready personal voices are available yet. Your uploaded voice must be ready before it can be used.</div>)}
                </div>

                <div className="form-section" style={{ marginTop: "32px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "15px" }}>
                    <div><label>Scenes</label><p style={{ marginTop: "5px" }}>Each scene becomes one part of your final video.</p></div>
                    <button type="button" className="generate-button" onClick={addCreatorScene} disabled={!creatorProject || creatorSaving}>+ Add Scene</button>
                  </div>

                  {creatorScenes.length === 0 ? (
                    <div className="preview-empty" style={{ marginTop: "20px" }}><div className="preview-icon"></div><h2>No scenes yet</h2><p>Add your first scene and write the script Aloko should speak.</p></div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "18px", marginTop: "20px" }}>
                      {creatorScenes.map(scene => (
                        <div key={scene.id} style={{ border: "1px solid rgba(255,255,255,0.12)", borderRadius: "16px", padding: "18px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                            <strong>Scene {scene.scene_order}</strong>
                            <button type="button" onClick={() => removeCreatorScene(scene.id)} disabled={creatorSaving} style={{ border: "none", background: "transparent", cursor: "pointer", color: "#ff8f8f" }}>Delete</button>
                          </div>
                          <textarea value={scene.script || ""} onChange={e => { const value=e.target.value; setCreatorScenes(prev => prev.map(item => item.id === scene.id ? {...item, script:value} : item)); }} onBlur={e => saveCreatorScene(scene.id, { script:e.target.value, avatar_id:selectedAvatarId ? Number(selectedAvatarId) : null, voice_id:creatorVoiceType === "personal" && creatorSelectedPersonalVoice ? Number(creatorSelectedPersonalVoice) : null })} maxLength={5000} rows={6} placeholder="Write what your avatar should say in this scene..." style={{ width: "100%", resize: "vertical" }} />
                          <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px", fontSize: "12px", opacity: 0.65 }}><span>Avatar: {selectedAvatar?.name || "Not selected"}</span><span>{(scene.script || "").length}/5000</span></div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <button className="generate-button" style={{ width: "100%", marginTop: "30px" }} disabled={creatorRenderLoading || creatorSaving || !creatorProject || !creatorScenes.length || !selectedAvatarId} onClick={handleCreatorRender}>{creatorRenderLoading ? "Rendering video..." : " Generate Video"}</button>
                {creatorRenderError && <div className="error" style={{ marginTop: "15px" }}>{creatorRenderError}</div>}
              </section>

              <section className="creator-panel" style={{ padding: "25px", position: "sticky", top: "20px" }}>
                <span className="result-label">VIDEO PREVIEW</span>
                {creatorRenderLoading ? (
                  <div className="preview-empty" style={{ minHeight: "430px" }}><div className="spinner"></div><h2>Creating your video</h2><p>Aloko is generating the voice, animating the avatar and combining your scenes.</p></div>
                ) : creatorRenderResult?.video_url ? (
                  <div><h2 style={{ marginTop: "10px" }}>Your video is ready</h2><video controls style={{ width: "100%", borderRadius: "14px", marginTop: "15px", display: "block" }} src={getMediaUrl(creatorRenderResult.video_url)} /><div className="result-actions" style={{ marginTop: "15px" }}><a href={getMediaUrl(creatorRenderResult.video_url)} download>Download MP4</a></div></div>
                ) : (
                  <div className="preview-empty" style={{ minHeight: "430px" }}><div className="preview-icon"></div><h2>Your final video</h2><p>Select an avatar, add your scenes and generate the video. The finished MP4 will appear here.</p></div>
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







