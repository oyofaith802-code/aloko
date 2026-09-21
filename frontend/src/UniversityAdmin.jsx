import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getUniversityPortalConfigs,
  getUniversityPortalSummary,
  getUniversityPortalSyncJobs,
  getUniversityPortalSchedules,
  getUniversityPortalWebhooks,
  getUniversityPortalLogs,
  createSchoolPortal,
  updateSchoolPortal,
  activateSchoolPortal,
  deactivateSchoolPortal,
  testSchoolPortal,
} from "./api";

const DEFAULT_UNIVERSITY_ID = 1;

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "sync", label: "Sync History" },
  { id: "schedules", label: "Schedules" },
  { id: "webhooks", label: "Webhooks" },
  { id: "logs", label: "Integration Logs" },
];

function formatDate(value) {
  if (!value) return "—";

  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function formatStatus(status) {
  if (!status) return "Unknown";

  return String(status)
    .replace(/[_-]/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusClass(status) {
  const value = String(status || "").toLowerCase();

  if (
    value.includes("success") ||
    value.includes("active") ||
    value.includes("processed") ||
    value.includes("completed") ||
    value === "ok"
  ) {
    return "success";
  }

  if (
    value.includes("failed") ||
    value.includes("error") ||
    value.includes("rejected")
  ) {
    return "danger";
  }

  if (
    value.includes("pending") ||
    value.includes("processing") ||
    value.includes("running")
  ) {
    return "warning";
  }

  return "neutral";
}

function StatusBadge({ status }) {
  return (
    <span className={`university-status university-status-${statusClass(status)}`}>
      {formatStatus(status)}
    </span>
  );
}

function EmptyState({ title, message }) {
  return (
    <div className="university-empty">
      <div className="university-empty-icon">◌</div>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

function LoadingState({ message = "Loading..." }) {
  return (
    <div className="university-loading">
      <div className="university-spinner" />
      <span>{message}</span>
    </div>
  );
}

function MetricCard({ label, value, description }) {
  return (
    <div className="university-metric">
      <div className="university-metric-label">{label}</div>
      <div className="university-metric-value">{value ?? "—"}</div>
      {description && (
        <div className="university-metric-description">{description}</div>
      )}
    </div>
  );
}

function DataTable({ columns, rows, emptyTitle, emptyMessage }) {
  if (!rows || rows.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        message={emptyMessage}
      />
    );
  }

  return (
    <div className="university-table-wrapper">
      <table className="university-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((row, index) => (
            <tr key={row.id ?? row.sync_id ?? row.webhook_id ?? index}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render
                    ? column.render(row)
                    : row[column.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function UniversityAdmin({ onBack }) {
  const [universityId, setUniversityId] = useState(
    DEFAULT_UNIVERSITY_ID
  );

  const [activeTab, setActiveTab] = useState("overview");

  const [configs, setConfigs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [syncJobs, setSyncJobs] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [logs, setLogs] = useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [portalEditorOpen, setPortalEditorOpen] = useState(false);
  const [portalSaving, setPortalSaving] = useState(false);
  const [portalTesting, setPortalTesting] = useState(false);
  const [portalToggling, setPortalToggling] = useState(false);

  const [portalForm, setPortalForm] = useState({
    portal_name: "",
    portal_url: "",
    integration_type: "api",
    api_base_url: "",
    api_key: "",
    client_id: "",
    client_secret: "",
    webhook_secret: "",
    sso_provider: "",
    sync_enabled: false,
    webhook_enabled: false,
  });

  const selectedPortal = useMemo(() => {
    if (!configs.length) return null;

    return configs[0];
  }, [configs]);

  const portalConfigId = selectedPortal?.id;

  const loadPortalData = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError("");

      try {
        const configResult =
          await getUniversityPortalConfigs(universityId);

        const configList = Array.isArray(configResult)
          ? configResult
          : Array.isArray(configResult?.data)
          ? configResult.data
          : Array.isArray(configResult?.configs)
          ? configResult.configs
          : [];

        setConfigs(configList);

        const selectedConfig = configList[0];

        if (!selectedConfig?.id) {
          setSummary(null);
          setSyncJobs([]);
          setSchedules([]);
          setWebhooks([]);
          setLogs([]);
          return;
        }

        const configId = selectedConfig.id;

        const [
          summaryResult,
          syncResult,
          schedulesResult,
          webhooksResult,
          logsResult,
        ] = await Promise.all([
          getUniversityPortalSummary(
            universityId,
            configId
          ),
          getUniversityPortalSyncJobs(universityId),
          getUniversityPortalSchedules(universityId),
          getUniversityPortalWebhooks(universityId),
          getUniversityPortalLogs(universityId),
        ]);

        setSummary(summaryResult);

        setSyncJobs(
          Array.isArray(syncResult)
            ? syncResult
            : Array.isArray(syncResult?.data)
            ? syncResult.data
            : Array.isArray(syncResult?.jobs)
            ? syncResult.jobs
            : []
        );

        setSchedules(
          Array.isArray(schedulesResult)
            ? schedulesResult
            : Array.isArray(schedulesResult?.data)
            ? schedulesResult.data
            : Array.isArray(schedulesResult?.schedules)
            ? schedulesResult.schedules
            : []
        );

        setWebhooks(
          Array.isArray(webhooksResult)
            ? webhooksResult
            : Array.isArray(webhooksResult?.data)
            ? webhooksResult.data
            : Array.isArray(webhooksResult?.webhooks)
            ? webhooksResult.webhooks
            : []
        );

        setLogs(
          Array.isArray(logsResult)
            ? logsResult
            : Array.isArray(logsResult?.data)
            ? logsResult.data
            : Array.isArray(logsResult?.logs)
            ? logsResult.logs
            : []
        );

        if (silent) {
          setNotice("University portal data refreshed.");
        }
      } catch (err) {
        setError(
          err?.message ||
            "Unable to load university portal information."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [universityId]
  );

  useEffect(() => {
    loadPortalData();
  }, [loadPortalData]);

  const portalStatus =
    selectedPortal?.status ||
    summary?.status ||
    "unknown";

  const syncCount = syncJobs.length;
  const scheduleCount = schedules.length;
  const webhookCount = webhooks.length;
  const logCount = logs.length;

  const successfulSyncs = useMemo(() => {
    return syncJobs.filter((job) => {
      const status = String(job.status || "").toLowerCase();

      return (
        status === "completed" ||
        status === "success" ||
        status === "successful"
      );
    }).length;
  }, [syncJobs]);

  const failedSyncs = useMemo(() => {
    return syncJobs.filter((job) => {
      const status = String(job.status || "").toLowerCase();

      return (
        status === "failed" ||
        status === "error"
      );
    }).length;
  }, [syncJobs]);

  const pendingSyncs = useMemo(() => {
    return syncJobs.filter((job) => {
      const status = String(job.status || "").toLowerCase();

      return (
        status === "pending" ||
        status === "processing" ||
        status === "running"
      );
    }).length;
  }, [syncJobs]);

  const handleRefresh = () => {
    setNotice("");
    loadPortalData({ silent: true });
  };
  const openPortalEditor = (portal = null) => {
    setNotice("");
    setError("");

    setPortalForm({
      portal_name: portal?.portal_name || portal?.name || "",
      portal_url: portal?.portal_url || portal?.url || "",
      integration_type: portal?.integration_type || "api",
      api_base_url: portal?.api_base_url || "",
      api_key: "",
      client_id: portal?.client_id || "",
      client_secret: "",
      webhook_secret: "",
      sso_provider: portal?.sso_provider || "",
      sync_enabled: Boolean(portal?.sync_enabled),
      webhook_enabled: Boolean(portal?.webhook_enabled),
    });

    setPortalEditorOpen(true);
  };

  const closePortalEditor = () => {
    if (portalSaving) return;
    setPortalEditorOpen(false);
  };

  const handlePortalFormChange = (event) => {
    const { name, value, type, checked } = event.target;

    setPortalForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSavePortal = async (event) => {
    event.preventDefault();

    if (!portalForm.portal_name.trim()) {
      setError("Portal name is required.");
      return;
    }

    setPortalSaving(true);
    setError("");
    setNotice("");

    try {
      const payload = {
        university_id: Number(universityId),
        portal_name: portalForm.portal_name.trim(),
        portal_url: portalForm.portal_url.trim() || null,
        integration_type: portalForm.integration_type,
        api_base_url: portalForm.api_base_url.trim() || null,
        client_id: portalForm.client_id.trim() || null,
        sso_provider: portalForm.sso_provider.trim() || null,
        sync_enabled: Boolean(portalForm.sync_enabled),
        webhook_enabled: Boolean(portalForm.webhook_enabled),
      };

      if (portalForm.api_key.trim()) {
        payload.api_key = portalForm.api_key.trim();
      }

      if (portalForm.client_secret.trim()) {
        payload.client_secret = portalForm.client_secret.trim();
      }

      if (portalForm.webhook_secret.trim()) {
        payload.webhook_secret = portalForm.webhook_secret.trim();
      }

      if (selectedPortal?.id) {
        await updateSchoolPortal(selectedPortal.id, payload);
        setNotice("University portal updated successfully.");
      } else {
        await createSchoolPortal(payload);
        setNotice("University portal linked successfully.");
      }

      setPortalEditorOpen(false);
      await loadPortalData({ silent: true });
    } catch (err) {
      setError(
        err?.message ||
          "Unable to save university portal configuration."
      );
    } finally {
      setPortalSaving(false);
    }
  };

  const handleTestPortal = async () => {
    if (!selectedPortal?.id) {
      setError("Save the portal configuration before testing it.");
      return;
    }

    setPortalTesting(true);
    setError("");
    setNotice("");

    try {
      const result = await testSchoolPortal(
        universityId,
        selectedPortal.id
      );

      setNotice(
        result?.message ||
          "University portal connection test completed."
      );

      await loadPortalData({ silent: true });
    } catch (err) {
      setError(
        err?.message ||
          "University portal connection test failed."
      );
    } finally {
      setPortalTesting(false);
    }
  };

  const handleTogglePortal = async () => {
    if (!selectedPortal?.id) {
      setError("Save the portal configuration first.");
      return;
    }

    setPortalToggling(true);
    setError("");
    setNotice("");

    try {
      const status = String(
        selectedPortal.status || ""
      ).toLowerCase();

      if (status === "active") {
        await deactivateSchoolPortal(
          universityId,
          selectedPortal.id
        );

        setNotice("University portal deactivated.");
      } else {
        await activateSchoolPortal(
          universityId,
          selectedPortal.id
        );

        setNotice("University portal activated.");
      }

      await loadPortalData({ silent: true });
    } catch (err) {
      setError(
        err?.message ||
          "Unable to change university portal status."
      );
    } finally {
      setPortalToggling(false);
    }
  };


  return (
    <div className="university-admin-page">
      {portalEditorOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 1000,
            background: "rgba(15, 23, 42, 0.55)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 20,
            overflowY: "auto",
          }}
        >
          <div
            className="university-card"
            style={{
              width: "min(760px, 100%)",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: 24,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 16,
                marginBottom: 20,
              }}
            >
              <div>
                <h2 style={{ margin: 0 }}>
                  {selectedPortal
                    ? "Edit University Portal"
                    : "Link University Portal"}
                </h2>

                <p
                  style={{
                    margin: "6px 0 0",
                    color: "#64748b",
                  }}
                >
                  Connect this university's existing academic portal
                  to Aloko.
                </p>
              </div>

              <button
                type="button"
                className="university-secondary-button"
                onClick={closePortalEditor}
                disabled={portalSaving}
              >
                Close
              </button>
            </div>

            <form onSubmit={handleSavePortal}>
              <div className="university-info-grid">
                <div>
                  <label className="university-info-label">
                    Portal Name
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    name="portal_name"
                    value={portalForm.portal_name}
                    onChange={handlePortalFormChange}
                    placeholder="University Student Portal"
                    required
                  />
                </div>

                <div>
                  <label className="university-info-label">
                    Integration Type
                  </label>

                  <select
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    name="integration_type"
                    value={portalForm.integration_type}
                    onChange={handlePortalFormChange}
                  >
                    <option value="api">REST API</option>
                    <option value="sso">SSO</option>
                    <option value="hybrid">Hybrid</option>
                  </select>
                </div>

                <div>
                  <label className="university-info-label">
                    Portal URL
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    name="portal_url"
                    value={portalForm.portal_url}
                    onChange={handlePortalFormChange}
                    placeholder="https://portal.example.edu"
                  />
                </div>

                <div>
                  <label className="university-info-label">
                    API Base URL
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    name="api_base_url"
                    value={portalForm.api_base_url}
                    onChange={handlePortalFormChange}
                    placeholder="https://api.example.edu"
                  />
                </div>

                <div>
                  <label className="university-info-label">
                    API Key
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    type="password"
                    name="api_key"
                    value={portalForm.api_key}
                    onChange={handlePortalFormChange}
                    placeholder={
                      selectedPortal
                        ? "Leave blank to keep existing key"
                        : "Portal API key"
                    }
                  />
                </div>

                <div>
                  <label className="university-info-label">
                    Client ID
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    name="client_id"
                    value={portalForm.client_id}
                    onChange={handlePortalFormChange}
                    placeholder="Optional OAuth/SSO client ID"
                  />
                </div>

                <div>
                  <label className="university-info-label">
                    Client Secret
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    type="password"
                    name="client_secret"
                    value={portalForm.client_secret}
                    onChange={handlePortalFormChange}
                    placeholder={
                      selectedPortal
                        ? "Leave blank to keep existing secret"
                        : "Optional client secret"
                    }
                  />
                </div>

                <div>
                  <label className="university-info-label">
                    SSO Provider
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    name="sso_provider"
                    value={portalForm.sso_provider}
                    onChange={handlePortalFormChange}
                    placeholder="Optional SSO provider"
                  />
                </div>

                <div>
                  <label className="university-info-label">
                    Webhook Secret
                  </label>

                  <input
                    className="university-id-input"
                    style={{ width: "100%", marginTop: 6 }}
                    type="password"
                    name="webhook_secret"
                    value={portalForm.webhook_secret}
                    onChange={handlePortalFormChange}
                    placeholder={
                      selectedPortal
                        ? "Leave blank to keep existing secret"
                        : "Optional webhook secret"
                    }
                  />
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  gap: 24,
                  flexWrap: "wrap",
                  marginTop: 20,
                  padding: 16,
                  background: "#f8fafc",
                  borderRadius: 10,
                }}
              >
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <input
                    type="checkbox"
                    name="sync_enabled"
                    checked={portalForm.sync_enabled}
                    onChange={handlePortalFormChange}
                  />
                  Enable automatic sync
                </label>

                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <input
                    type="checkbox"
                    name="webhook_enabled"
                    checked={portalForm.webhook_enabled}
                    onChange={handlePortalFormChange}
                  />
                  Enable webhooks
                </label>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: 10,
                  marginTop: 22,
                }}
              >
                <button
                  type="button"
                  className="university-secondary-button"
                  onClick={closePortalEditor}
                  disabled={portalSaving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="university-primary-button"
                  disabled={portalSaving}
                >
                  {portalSaving
                    ? "Saving..."
                    : selectedPortal
                    ? "Save Changes"
                    : "Link Portal"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      <style>{`
        .university-admin-page {
          min-height: 100vh;
          background:
            radial-gradient(circle at top right, rgba(99,102,241,.10), transparent 32%),
            linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
          color: #172033;
          padding: 28px;
          box-sizing: border-box;
        }

        .university-admin-container {
          max-width: 1400px;
          margin: 0 auto;
        }

        .university-admin-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 20px;
          margin-bottom: 24px;
        }

        .university-admin-title-area {
          display: flex;
          gap: 16px;
          align-items: flex-start;
        }

        .university-back-button,
        .university-refresh-button {
          border: 1px solid #d8dee9;
          background: white;
          color: #172033;
          border-radius: 10px;
          padding: 10px 14px;
          cursor: pointer;
          font-weight: 600;
        }

        .university-back-button:hover,
        .university-refresh-button:hover {
          background: #f1f5f9;
        }

        .university-admin-title {
          margin: 0;
          font-size: 30px;
          line-height: 1.15;
          letter-spacing: -.7px;
        }

        .university-admin-subtitle {
          margin: 7px 0 0;
          color: #64748b;
          font-size: 14px;
        }

        .university-header-actions {
          display: flex;
          gap: 10px;
          align-items: center;
        }

        .university-id-input {
          width: 105px;
          border: 1px solid #d8dee9;
          border-radius: 10px;
          padding: 10px 12px;
          background: white;
          outline: none;
        }

        .university-card {
          background: rgba(255,255,255,.94);
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          box-shadow: 0 8px 30px rgba(15,23,42,.05);
        }

        .university-portal-card {
          padding: 22px;
          margin-bottom: 20px;
        }

        .university-portal-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
        }

        .university-portal-name {
          font-size: 20px;
          font-weight: 750;
          margin-bottom: 6px;
        }

        .university-portal-url {
          color: #64748b;
          font-size: 13px;
          word-break: break-all;
        }

        .university-portal-meta {
          display: flex;
          gap: 10px;
          align-items: center;
          flex-wrap: wrap;
        }

        .university-status {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 5px 10px;
          font-size: 12px;
          font-weight: 700;
          white-space: nowrap;
        }

        .university-status-success {
          background: #dcfce7;
          color: #166534;
        }

        .university-status-danger {
          background: #fee2e2;
          color: #991b1b;
        }

        .university-status-warning {
          background: #fef3c7;
          color: #92400e;
        }

        .university-status-neutral {
          background: #e2e8f0;
          color: #475569;
        }

        .university-metrics {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 20px;
        }

        .university-metric {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 14px;
          padding: 18px;
        }

        .university-metric-label {
          color: #64748b;
          font-size: 13px;
          font-weight: 600;
        }

        .university-metric-value {
          margin-top: 8px;
          font-size: 28px;
          font-weight: 800;
          letter-spacing: -.5px;
        }

        .university-metric-description {
          margin-top: 4px;
          color: #94a3b8;
          font-size: 12px;
        }

        .university-tabs {
          display: flex;
          gap: 4px;
          padding: 5px;
          margin-bottom: 18px;
          overflow-x: auto;
          background: #e8edf4;
          border-radius: 13px;
        }

        .university-tab {
          border: 0;
          background: transparent;
          color: #64748b;
          border-radius: 9px;
          padding: 10px 15px;
          font-weight: 650;
          cursor: pointer;
          white-space: nowrap;
        }

        .university-tab.active {
          background: white;
          color: #172033;
          box-shadow: 0 2px 8px rgba(15,23,42,.08);
        }

        .university-content-card {
          padding: 22px;
        }

        .university-section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          margin-bottom: 18px;
        }

        .university-section-title {
          margin: 0;
          font-size: 19px;
        }

        .university-section-description {
          margin: 5px 0 0;
          color: #64748b;
          font-size: 13px;
        }

        .university-table-wrapper {
          overflow-x: auto;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
        }

        .university-table {
          width: 100%;
          border-collapse: collapse;
          min-width: 720px;
        }

        .university-table th {
          text-align: left;
          background: #f8fafc;
          color: #64748b;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: .4px;
          padding: 12px 14px;
          border-bottom: 1px solid #e2e8f0;
        }

        .university-table td {
          padding: 13px 14px;
          border-bottom: 1px solid #edf2f7;
          font-size: 13px;
          vertical-align: top;
        }

        .university-table tr:last-child td {
          border-bottom: 0;
        }

        .university-empty {
          text-align: center;
          padding: 55px 20px;
          color: #64748b;
        }

        .university-empty-icon {
          width: 45px;
          height: 45px;
          border-radius: 50%;
          background: #f1f5f9;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 12px;
          font-size: 25px;
        }

        .university-empty h3 {
          margin: 0 0 6px;
          color: #334155;
        }

        .university-empty p {
          margin: 0;
          font-size: 13px;
        }

        .university-loading {
          min-height: 250px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          color: #64748b;
        }

        .university-spinner {
          width: 18px;
          height: 18px;
          border: 2px solid #dbe3ee;
          border-top-color: #4f46e5;
          border-radius: 50%;
          animation: university-spin .8s linear infinite;
        }

        @keyframes university-spin {
          to {
            transform: rotate(360deg);
          }
        }

        .university-alert {
          padding: 13px 15px;
          border-radius: 11px;
          margin-bottom: 18px;
          font-size: 13px;
          font-weight: 600;
        }

        .university-alert-error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fecaca;
        }

        .university-alert-success {
          background: #dcfce7;
          color: #166534;
          border: 1px solid #bbf7d0;
        }

        .university-info-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 14px;
        }

        .university-info-item {
          padding: 15px;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          background: #fafcff;
        }

        .university-info-label {
          color: #64748b;
          font-size: 12px;
          margin-bottom: 5px;
        }

        .university-info-value {
          font-size: 14px;
          font-weight: 650;
          word-break: break-word;
        }

        @media (max-width: 900px) {
          .university-metrics {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .university-admin-header,
          .university-portal-top {
            flex-direction: column;
            align-items: stretch;
          }

          .university-header-actions {
            flex-wrap: wrap;
          }
        }

        @media (max-width: 600px) {
          .university-admin-page {
            padding: 15px;
          }

          .university-metrics,
          .university-info-grid {
            grid-template-columns: 1fr;
          }

          .university-admin-title {
            font-size: 24px;
          }
        }
      `}</style>

      <div className="university-admin-container">

        <header className="university-admin-header">
          <div className="university-admin-title-area">
            <button
              className="university-back-button"
              onClick={onBack}
              type="button"
            >
              ← Back
            </button>

            <div>
              <h1 className="university-admin-title">
                University AI
              </h1>

              <p className="university-admin-subtitle">
                University administration and portal integration
              </p>
            </div>
          </div>

          <div className="university-header-actions">
            <input
              className="university-id-input"
              type="number"
              min="1"
              value={universityId}
              onChange={(event) =>
                setUniversityId(
                  Number(event.target.value) || 1
                )
              }
              title="University ID"
            />

            <button
              className="university-refresh-button"
              onClick={handleRefresh}
              disabled={refreshing}
              type="button"
            >
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>
          </div>
        </header>

        {error && (
          <div className="university-alert university-alert-error">
            {error}
          </div>
        )}

        {notice && (
          <div className="university-alert university-alert-success">
            {notice}
          </div>
        )}

        {loading ? (
          <div className="university-card">
            <LoadingState message="Loading university portal..." />
          </div>
        ) : (
          <>
            {!selectedPortal ? (
              <div className="university-card">
                <EmptyState
                  title="No university portal connected"
                  message="No portal configuration was found for this university."
                />
                <div
                  className="portal-management-actions"
                  style={{
                    marginTop: 18,
                    display: "flex",
                    justifyContent: "center",
                  }}
                >
                  <button
                    type="button"
                    className="university-primary-button"
                    onClick={() => openPortalEditor()}
                  >
                    Link University Portal
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="university-card university-portal-card">
                  <div className="university-portal-top">
                    <div>
                      <div className="university-portal-name">
                        {selectedPortal.portal_name ||
                          "University Portal"}
                      </div>

                      <div className="university-portal-url">
                        {selectedPortal.api_base_url ||
                          selectedPortal.portal_url ||
                          "No portal URL configured"}
                      </div>
                    </div>

                    <div className="university-portal-meta">
                      <StatusBadge status={portalStatus} />

                      {selectedPortal.sync_enabled && (
                        <span className="university-status university-status-success">
                          Sync Enabled
                        </span>
                      )}

                      {selectedPortal.webhook_enabled && (
                        <span className="university-status university-status-success">
                          Webhooks Enabled
                        </span>
                      )}
                    </div>
                    <div
                      className="portal-management-actions"
                      style={{
                        display: "flex",
                        gap: 8,
                        flexWrap: "wrap",
                        justifyContent: "flex-end",
                        marginTop: 14,
                      }}
                    >
                      <button
                        type="button"
                        className="university-secondary-button"
                        onClick={() => openPortalEditor(selectedPortal)}
                      >
                        Edit Portal
                      </button>

                      <button
                        type="button"
                        className="university-secondary-button"
                        onClick={handleTestPortal}
                        disabled={portalTesting}
                      >
                        {portalTesting ? "Testing..." : "Test Connection"}
                      </button>

                      <button
                        type="button"
                        className="university-secondary-button"
                        onClick={handleTogglePortal}
                        disabled={portalToggling}
                      >
                        {portalToggling
                          ? "Updating..."
                          : String(selectedPortal.status || "").toLowerCase() === "active"
                          ? "Deactivate"
                          : "Activate"}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="university-metrics">
                  <MetricCard
                    label="Sync Jobs"
                    value={syncCount}
                    description={`${successfulSyncs} successful`}
                  />

                  <MetricCard
                    label="Pending / Running"
                    value={pendingSyncs}
                    description="Currently active jobs"
                  />

                  <MetricCard
                    label="Failed Syncs"
                    value={failedSyncs}
                    description="Jobs requiring attention"
                  />

                  <MetricCard
                    label="Webhooks"
                    value={webhookCount}
                    description={`${scheduleCount} schedules`}
                  />
                </div>

                <nav className="university-tabs">
                  {TABS.map((tab) => (
                    <button
                      key={tab.id}
                      type="button"
                      className={`university-tab ${
                        activeTab === tab.id
                          ? "active"
                          : ""
                      }`}
                      onClick={() =>
                        setActiveTab(tab.id)
                      }
                    >
                      {tab.label}
                    </button>
                  ))}
                </nav>

                <div className="university-card university-content-card">

                  {activeTab === "overview" && (
                    <>
                      <div className="university-section-header">
                        <div>
                          <h2 className="university-section-title">
                            Portal Overview
                          </h2>

                          <p className="university-section-description">
                            Connection and integration status for
                            this university.
                          </p>
                        </div>
                      </div>

                      <div className="university-info-grid">
                        <div className="university-info-item">
                          <div className="university-info-label">
                            Portal Name
                          </div>

                          <div className="university-info-value">
                            {selectedPortal.portal_name || "—"}
                          </div>
                        </div>

                        <div className="university-info-item">
                          <div className="university-info-label">
                            Integration Type
                          </div>

                          <div className="university-info-value">
                            {selectedPortal.integration_type || "—"}
                          </div>
                        </div>

                        <div className="university-info-item">
                          <div className="university-info-label">
                            Portal Status
                          </div>

                          <div className="university-info-value">
                            <StatusBadge status={portalStatus} />
                          </div>
                        </div>

                        <div className="university-info-item">
                          <div className="university-info-label">
                            Last Sync
                          </div>

                          <div className="university-info-value">
                            {formatDate(
                              selectedPortal.last_sync_at
                            )}
                          </div>
                        </div>

                        <div className="university-info-item">
                          <div className="university-info-label">
                            Sync
                          </div>

                          <div className="university-info-value">
                            {selectedPortal.sync_enabled
                              ? "Enabled"
                              : "Disabled"}
                          </div>
                        </div>

                        <div className="university-info-item">
                          <div className="university-info-label">
                            Webhooks
                          </div>

                          <div className="university-info-value">
                            {selectedPortal.webhook_enabled
                              ? "Enabled"
                              : "Disabled"}
                          </div>
                        </div>

                        <div className="university-info-item">
                          <div className="university-info-label">
                            SSO Provider
                          </div>

                          <div className="university-info-value">
                            {selectedPortal.sso_provider || "—"}
                          </div>
                        </div>

                        <div className="university-info-item">
                          <div className="university-info-label">
                            Portal Config ID
                          </div>

                          <div className="university-info-value">
                            {portalConfigId ?? "—"}
                          </div>
                        </div>
                      </div>

                      {summary && (
                        <div style={{ marginTop: 22 }}>
                          <div className="university-section-header">
                            <div>
                              <h2 className="university-section-title">
                                Integration Summary
                              </h2>

                              <p className="university-section-description">
                                Current synchronization statistics
                                returned by the backend.
                              </p>
                            </div>
                          </div>

                          <div className="university-info-grid">
                            {Object.entries(summary)
                              .filter(
                                ([, value]) =>
                                  value !== null &&
                                  typeof value !== "object"
                              )
                              .slice(0, 8)
                              .map(([key, value]) => (
                                <div
                                  className="university-info-item"
                                  key={key}
                                >
                                  <div className="university-info-label">
                                    {formatStatus(key)}
                                  </div>

                                  <div className="university-info-value">
                                    {String(value)}
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {activeTab === "sync" && (
                    <>
                      <div className="university-section-header">
                        <div>
                          <h2 className="university-section-title">
                            Synchronization History
                          </h2>

                          <p className="university-section-description">
                            Monitor portal synchronization jobs,
                            retries, failures and completion.
                          </p>
                        </div>
                      </div>

                      <DataTable
                        rows={syncJobs}
                        emptyTitle="No sync jobs"
                        emptyMessage="Synchronization jobs will appear here when the portal sync runs."
                        columns={[
                          {
                            key: "id",
                            label: "ID",
                          },
                          {
                            key: "sync_type",
                            label: "Type",
                            render: (row) =>
                              formatStatus(
                                row.sync_type ||
                                  row.entity_type ||
                                  row.type
                              ),
                          },
                          {
                            key: "status",
                            label: "Status",
                            render: (row) => (
                              <StatusBadge
                                status={row.status}
                              />
                            ),
                          },
                          {
                            key: "retry_count",
                            label: "Retries",
                            render: (row) =>
                              row.retry_count ?? 0,
                          },
                          {
                            key: "created_at",
                            label: "Created",
                            render: (row) =>
                              formatDate(
                                row.created_at
                              ),
                          },
                          {
                            key: "completed_at",
                            label: "Completed",
                            render: (row) =>
                              formatDate(
                                row.completed_at
                              ),
                          },
                        ]}
                      />
                    </>
                  )}

                  {activeTab === "schedules" && (
                    <>
                      <div className="university-section-header">
                        <div>
                          <h2 className="university-section-title">
                            Sync Schedules
                          </h2>

                          <p className="university-section-description">
                            Automatic synchronization schedules
                            configured for the university.
                          </p>
                        </div>
                      </div>

                      <DataTable
                        rows={schedules}
                        emptyTitle="No schedules"
                        emptyMessage="No automatic synchronization schedules are configured."
                        columns={[
                          {
                            key: "id",
                            label: "ID",
                          },
                          {
                            key: "sync_type",
                            label: "Type",
                            render: (row) =>
                              formatStatus(
                                row.sync_type ||
                                  row.entity_type ||
                                  row.type
                              ),
                          },
                          {
                            key: "status",
                            label: "Status",
                            render: (row) => (
                              <StatusBadge
                                status={
                                  row.status ||
                                  (row.enabled
                                    ? "enabled"
                                    : "disabled")
                                }
                              />
                            ),
                          },
                          {
                            key: "interval_minutes",
                            label: "Interval",
                            render: (row) =>
                              row.interval_minutes
                                ? `${row.interval_minutes} min`
                                : row.cron_expression ||
                                  row.cron ||
                                  "—",
                          },
                          {
                            key: "last_run_at",
                            label: "Last Run",
                            render: (row) =>
                              formatDate(
                                row.last_run_at
                              ),
                          },
                          {
                            key: "next_run_at",
                            label: "Next Run",
                            render: (row) =>
                              formatDate(
                                row.next_run_at
                              ),
                          },
                        ]}
                      />
                    </>
                  )}

                  {activeTab === "webhooks" && (
                    <>
                      <div className="university-section-header">
                        <div>
                          <h2 className="university-section-title">
                            Webhook History
                          </h2>

                          <p className="university-section-description">
                            Incoming events received from the
                            university portal.
                          </p>
                        </div>
                      </div>

                      <DataTable
                        rows={webhooks}
                        emptyTitle="No webhooks"
                        emptyMessage="Incoming portal events will appear here."
                        columns={[
                          {
                            key: "id",
                            label: "ID",
                          },
                          {
                            key: "event_type",
                            label: "Event",
                            render: (row) =>
                              formatStatus(
                                row.event_type
                              ),
                          },
                          {
                            key: "event_reference",
                            label: "Reference",
                            render: (row) =>
                              row.event_reference ||
                              "—",
                          },
                          {
                            key: "status",
                            label: "Status",
                            render: (row) => (
                              <StatusBadge
                                status={row.status}
                              />
                            ),
                          },
                          {
                            key: "created_at",
                            label: "Received",
                            render: (row) =>
                              formatDate(
                                row.created_at
                              ),
                          },
                          {
                            key: "processed_at",
                            label: "Processed",
                            render: (row) =>
                              formatDate(
                                row.processed_at
                              ),
                          },
                        ]}
                      />
                    </>
                  )}

                  {activeTab === "logs" && (
                    <>
                      <div className="university-section-header">
                        <div>
                          <h2 className="university-section-title">
                            Integration Logs
                          </h2>

                          <p className="university-section-description">
                            Technical activity and integration
                            events for administrators.
                          </p>
                        </div>
                      </div>

                      <DataTable
                        rows={logs}
                        emptyTitle="No integration logs"
                        emptyMessage="Portal integration activity will appear here."
                        columns={[
                          {
                            key: "id",
                            label: "ID",
                          },
                          {
                            key: "action",
                            label: "Action",
                            render: (row) =>
                              formatStatus(
                                row.action
                              ),
                          },
                          {
                            key: "status",
                            label: "Status",
                            render: (row) => (
                              <StatusBadge
                                status={row.status}
                              />
                            ),
                          },
                          {
                            key: "message",
                            label: "Message",
                            render: (row) => (
                              <span
                                style={{
                                  display: "block",
                                  maxWidth: 520,
                                  whiteSpace: "normal",
                                  wordBreak: "break-word",
                                }}
                              >
                                {row.message || "—"}
                              </span>
                            ),
                          },
                          {
                            key: "created_at",
                            label: "Time",
                            render: (row) =>
                              formatDate(
                                row.created_at
                              ),
                          },
                        ]}
                      />
                    </>
                  )}

                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

