import React, { useCallback, useEffect, useState } from "react";
import {
  addSupportKnowledge,
  createSupportWorkspace,
  deleteSupportKnowledge,
  getSupportKnowledge,
  getSupportSubscriptionStatus,
  getSupportWorkspaces,
  getSupportWidgetSettings,
  saveSupportWidgetSettings,
  startSupportCheckout,
  testSupportChat,
  verifySupportCheckout,
} from "./api.js";

const styles = {
  page: { minHeight: "100vh", padding: "28px 18px", background: "var(--page-bg, #f5f7fb)", color: "var(--text-color, #171923)" },
  container: { maxWidth: 1050, margin: "0 auto" },
  panel: { background: "var(--card-bg, #fff)", border: "1px solid var(--border-color, #e5e7eb)", borderRadius: 16, padding: 22, marginBottom: 18 },
  field: { width: "100%", boxSizing: "border-box", padding: 12, border: "1px solid #d1d5db", borderRadius: 9, marginTop: 6, marginBottom: 12, font: "inherit" },
  button: { padding: "11px 16px", border: 0, borderRadius: 9, background: "#4f46e5", color: "#fff", fontWeight: 650, cursor: "pointer" },
  secondary: { padding: "10px 14px", border: "1px solid #d1d5db", borderRadius: 9, background: "transparent", color: "inherit", cursor: "pointer" },
};

export default function CustomerSupportAI({ onBack }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [knowledge, setKnowledge] = useState([]);
  const [subscription, setSubscription] = useState({ active: false });
  const [form, setForm] = useState({ name: "", industry: "", description: "" });
  const [knowledgeForm, setKnowledgeForm] = useState({ title: "", category: "general", content: "" });
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [currency, setCurrency] = useState("NGN");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [widgetSettings, setWidgetSettings] = useState({
    allowed_domains: [],
    is_enabled: false,
    embed_code: "",
  });
  const [domainInput, setDomainInput] = useState("");
  const [widgetLoading, setWidgetLoading] = useState(false);

  const selectedWorkspace = workspaces.find((w) => String(w.id) === String(workspaceId));

  const loadKnowledge = useCallback(async (id) => {
    if (!id) {
      setKnowledge([]);
      return;
    }
    const result = await getSupportKnowledge(id);
    setKnowledge(result.knowledge || []);
  }, []);

  const refreshStatus = useCallback(async () => {
    const result = await getSupportSubscriptionStatus();
    setSubscription(result);
  }, []);

  const loadWorkspaces = useCallback(async () => {
    const result = await getSupportWorkspaces();
    const items = result.workspaces || [];
    setWorkspaces(items);
    setWorkspaceId((current) => {
      if (current && items.some((w) => String(w.id) === String(current))) return current;
      return items.length ? String(items[0].id) : "";
    });
  }, []);

  useEffect(() => {
    let alive = true;

    async function initialize() {
      setLoading(true);
      setError("");
      try {
        const params = new URLSearchParams(window.location.search);
        const reference = params.get("reference") || params.get("trxref");

        if (window.location.pathname.replace(/\/+$/, "") === "/billing/callback") {
          if (!reference) {
            setNotice("Payment return received, but no payment reference was provided. Check your subscription status.");
          } else {
            await verifySupportCheckout(reference);
            setNotice("Payment verified. Your Customer Support AI subscription is active for 30 days.");
          }
          window.history.replaceState({}, "", "/");
        }

        await Promise.all([loadWorkspaces(), refreshStatus()]);
      } catch (err) {
        if (alive) setError(err.message || "Unable to load Customer Support AI.");
      } finally {
        if (alive) setLoading(false);
      }
    }

    initialize();
    return () => { alive = false; };
  }, [loadWorkspaces, refreshStatus]);

  useEffect(() => {
    let active = true;
    setWidgetSettings({ allowed_domains: [], is_enabled: false, embed_code: "" });
    if (workspaceId) {
      getSupportWidgetSettings(workspaceId)
        .then((result) => {
          if (active) setWidgetSettings(result);
        })
        .catch((err) => {
          if (active) setError(err.message || "Unable to load widget settings.");
        });
    }
    return () => { active = false; };
  }, [workspaceId]);

  useEffect(() => {
    setReply("");
    setConversationId(null);
    setError("");
    if (workspaceId) {
      loadKnowledge(workspaceId).catch((err) => setError(err.message));
    } else {
      setKnowledge([]);
    }
  }, [workspaceId, loadKnowledge]);

  async function handleCreateWorkspace(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const result = await createSupportWorkspace({
        name: form.name.trim(),
        industry: form.industry.trim(),
        description: form.description.trim() || null,
      });
      const created = result.workspace;
      setWorkspaces((items) => [...items, created]);
      setWorkspaceId(String(created.id));
      setForm({ name: "", industry: "", description: "" });
      setNotice("Workspace created. You can add knowledge before testing the AI.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddKnowledge(event) {
    event.preventDefault();
    if (!workspaceId) return;
    setLoading(true);
    setError("");
    try {
      await addSupportKnowledge(workspaceId, {
        title: knowledgeForm.title.trim(),
        category: knowledgeForm.category.trim() || "general",
        content: knowledgeForm.content.trim(),
      });
      setKnowledgeForm({ title: "", category: "general", content: "" });
      await loadKnowledge(workspaceId);
      setNotice("Knowledge entry saved.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteKnowledge(id) {
    if (!workspaceId) return;
    setLoading(true);
    setError("");
    try {
      await deleteSupportKnowledge(workspaceId, id);
      await loadKnowledge(workspaceId);
      setNotice("Knowledge entry deactivated.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleTestChat(event) {
    event.preventDefault();
    if (!workspaceId || !message.trim()) return;
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const result = await testSupportChat(workspaceId, {
        message: message.trim(),
        ...(conversationId ? { conversation_id: conversationId } : {}),
      });
      setConversationId(result.conversation_id);
      setReply(result.reply);
      setMessage("");
      setNotice(result.note || "AI test completed.");
    } catch (err) {
      setError(err.message);
      if (err.status === 402 || err.code === "subscription_required") {
        setNotice("Your free AI test has been used. Choose a plan below to continue.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleCheckout() {
    setLoading(true);
    setError("");
    try {
      const result = await startSupportCheckout(currency);
      if (!result.authorization_url) throw new Error("Checkout link was not returned by the payment provider.");
      window.location.assign(result.authorization_url);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  return (
    <main style={styles.page}>
      <div style={styles.container}>
        <button style={styles.secondary} onClick={onBack}>← Back to Aloko</button>
        <header style={{ margin: "22px 0" }}>
          <p style={{ color: "#6366f1", fontWeight: 700, marginBottom: 6 }}>ALOKO BUSINESS AI</p>
          <h1 style={{ margin: "0 0 8px" }}>Customer Support AI</h1>
          <p style={{ margin: 0, lineHeight: 1.6 }}>
            Build a company knowledge base and test AI-powered customer replies.
            WhatsApp delivery and live customer messaging are not included in this test workspace.
          </p>
        </header>

        {error && <div role="alert" style={{ ...styles.panel, borderColor: "#ef4444", color: "#b91c1c" }}>{error}</div>}
        {notice && <div role="status" style={{ ...styles.panel, borderColor: "#a5b4fc" }}>{notice}</div>}
        {loading && <p aria-live="polite">Working…</p>}

        <section style={styles.panel}>
          <h2 style={{ marginTop: 0 }}>Your workspace</h2>
          {workspaces.length > 0 && (
            <label style={{ display: "block", marginBottom: 18 }}>
              Select workspace
              <select style={styles.field} value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)}>
                {workspaces.map((w) => <option key={w.id} value={w.id}>{w.name} — {w.industry}</option>)}
              </select>
            </label>
          )}

          {selectedWorkspace && (
            <div style={{ marginBottom: 18 }}>
              <h3>{selectedWorkspace.name}</h3>
              <p>{selectedWorkspace.industry}</p>
              {selectedWorkspace.description && <p>{selectedWorkspace.description}</p>}
            </div>
          )}

          <h3>Create a workspace</h3>
          <form onSubmit={handleCreateWorkspace}>
            <label>Company name
              <input style={styles.field} required maxLength={160} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
            <label>Industry
              <input style={styles.field} required maxLength={120} placeholder="e.g. Retail, education, healthcare" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
            </label>
            <label>Company description
              <textarea style={styles.field} rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </label>
            <button style={styles.button} disabled={loading} type="submit">Create workspace</button>
          </form>
        </section>

        {selectedWorkspace && <>
          <section style={styles.panel}>
            <h2 style={{ marginTop: 0 }}>Website chat widget</h2>
            <p>Embed Aloko Customer Support AI on your own website. An active Customer Support AI subscription is required for visitor chats.</p>
            <form onSubmit={async (event) => {
              event.preventDefault();
              setWidgetLoading(true);
              setError("");
              setNotice("");
              try {
                const result = await saveSupportWidgetSettings(workspaceId, {
                  allowed_domains: widgetSettings.allowed_domains,
                  is_enabled: widgetSettings.is_enabled,
                });
                setWidgetSettings((current) => ({ ...current, ...result }));
                setNotice(result.is_enabled ? "Website widget enabled." : "Website widget settings saved.");
              } catch (err) {
                setError(err.message || "Unable to save widget settings.");
              } finally {
                setWidgetLoading(false);
              }
            }}>
              <label style={{ display: "block" }}>Allowed website domain
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <input style={{ ...styles.field, flex: "1 1 240px" }}
                    placeholder="example.com"
                    value={domainInput}
                    onChange={(event) => setDomainInput(event.target.value)}
                    aria-label="Website domain to allow" />
                  <button type="button" style={styles.secondary} disabled={widgetLoading || !domainInput.trim()}
                    onClick={() => {
                      const value = domainInput.trim().replace(/^https?:\/\//i, "").replace(/\/$/, "");
                      if (value && !widgetSettings.allowed_domains.includes(value)) {
                        setWidgetSettings((current) => ({
                          ...current,
                          allowed_domains: [...current.allowed_domains, value],
                        }));
                      }
                      setDomainInput("");
                    }}>Add domain</button>
                </div>
              </label>
              {widgetSettings.allowed_domains.map((domain) => (
                <div key={domain} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "8px 0" }}>
                  <span>{domain}</span>
                  <button type="button" style={styles.secondary} onClick={() => setWidgetSettings((current) => ({
                    ...current,
                    allowed_domains: current.allowed_domains.filter((item) => item !== domain),
                  }))}>Remove</button>
                </div>
              ))}
              <label style={{ display: "flex", gap: 10, alignItems: "center", margin: "14px 0" }}>
                <input type="checkbox" checked={Boolean(widgetSettings.is_enabled)}
                  onChange={(event) => setWidgetSettings((current) => ({ ...current, is_enabled: event.target.checked }))} />
                Enable website widget
              </label>
              <button style={styles.button} type="submit" disabled={widgetLoading}>
                {widgetLoading ? "Saving?" : "Save widget settings"}
              </button>
            </form>
            {widgetSettings.embed_code && <>
              <h3>Embed code</h3>
              <textarea readOnly rows={3} style={styles.field} value={widgetSettings.embed_code} />
              <button type="button" style={styles.secondary}
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(widgetSettings.embed_code);
                    setNotice("Embed code copied.");
                  } catch {
                    setError("Clipboard access failed. Select and copy the embed code manually.");
                  }
                }}>Copy embed code</button>
            </>}
          </section>

          <section style={styles.panel}>
            <h2 style={{ marginTop: 0 }}>Knowledge base</h2>
            <p>Add accurate information that the AI can use when responding to customer questions.</p>
            <form onSubmit={handleAddKnowledge}>
              <label>Entry title
                <input style={styles.field} required maxLength={200} value={knowledgeForm.title} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, title: e.target.value })} />
              </label>
              <label>Category
                <input style={styles.field} maxLength={80} value={knowledgeForm.category} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, category: e.target.value })} />
              </label>
              <label>Information
                <textarea style={styles.field} required rows={5} value={knowledgeForm.content} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, content: e.target.value })} />
              </label>
              <button style={styles.button} disabled={loading} type="submit">Save knowledge</button>
            </form>

            <h3>Saved entries ({knowledge.length})</h3>
            {knowledge.length === 0 && <p>No knowledge entries yet.</p>}
            {knowledge.map((item) => (
              <article key={item.id} style={{ borderTop: "1px solid #e5e7eb", padding: "12px 0" }}>
                <strong>{item.title}</strong>
                <p style={{ whiteSpace: "pre-wrap" }}>{item.content}</p>
                <button type="button" style={styles.secondary} disabled={loading} onClick={() => handleDeleteKnowledge(item.id)}>Deactivate entry</button>
              </article>
            ))}
          </section>

          <section style={styles.panel}>
            <h2 style={{ marginTop: 0 }}>Test your AI support assistant</h2>
            <p>One free test chat is available per account. Add knowledge first for more relevant answers.</p>
            <form onSubmit={handleTestChat}>
              <label>Your test question
                <textarea style={styles.field} rows={3} required value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Ask about your company's products, policies or services…" />
              </label>
              <button style={styles.button} type="submit" disabled={loading}>Send test message</button>
            </form>
            {reply && (
              <div style={{ marginTop: 18, padding: 16, background: "var(--muted-bg, #f8fafc)", borderRadius: 12 }}>
                <strong>AI reply</strong>
                <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.7 }}>{reply}</p>
              </div>
            )}
          </section>
        </>}

        <section style={styles.panel}>
          <h2 style={{ marginTop: 0 }}>Customer Support AI subscription</h2>
          <p>
            {subscription.active
              ? `Subscription active until ${subscription.period_end ? new Date(subscription.period_end).toLocaleString() : "the displayed expiry date"}.`
              : "Your subscription includes 30 days of Customer Support AI access after verified payment."}
          </p>
          <p><strong>₦5,000 / 30 days</strong> or <strong>$5 / 30 days</strong>. This is a one-time payment, not automatic renewal.</p>
          <label>Payment currency
            <select style={styles.field} value={currency} onChange={(e) => setCurrency(e.target.value)}>
              <option value="NGN">NGN — ₦5,000</option>
              <option value="USD">USD — $5</option>
            </select>
          </label>
          <button style={styles.button} disabled={loading || subscription.active} onClick={handleCheckout}>
            {subscription.active ? "Subscription active" : `Pay ${currency === "NGN" ? "₦5,000" : "$5"} with Paystack`}
          </button>
          <button style={{ ...styles.secondary, marginLeft: 8 }} disabled={loading} onClick={() => refreshStatus().catch((err) => setError(err.message))}>
            Refresh subscription
          </button>
          <p style={{ fontSize: 13, lineHeight: 1.6, opacity: 0.8 }}>
            Paid access is enabled only after the server confirms the payment with Paystack.
            Available currencies and card acceptance depend on your Paystack account configuration.
          </p>
        </section>
      </div>
    </main>
  );
}
