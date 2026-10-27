import json
import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.billing.models import AlokoSubscription
from app.core.security import get_current_user
from app.customer_support.agent import generate_support_reply
from app.customer_support.models import (
    SupportConversation,
    SupportKnowledgeItem,
    SupportMessage,
    SupportWidgetConfig,
    SupportWorkspace,
)
from app.database.connection import get_db
from app.models.user import User

router = APIRouter(prefix="/customer-support/widget", tags=["Customer Support Website Widget"])


class WidgetSettings(BaseModel):
    allowed_domains: list[str] = Field(default_factory=list, max_length=30)
    is_enabled: bool = True


class WidgetChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: int | None = None
    visitor_token: str | None = Field(default=None, min_length=20, max_length=100)


def _owned_workspace(workspace_id: int, user: User, db: Session):
    workspace = db.query(SupportWorkspace).filter(
        SupportWorkspace.id == workspace_id,
        SupportWorkspace.user_id == user.id,
        SupportWorkspace.status == "active",
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return workspace


def _active_subscription(user_id: int, db: Session) -> bool:
    now = datetime.now(timezone.utc)
    row = db.query(AlokoSubscription).filter(
        AlokoSubscription.user_id == user_id,
        AlokoSubscription.product == "customer_support",
        AlokoSubscription.status == "active",
        AlokoSubscription.period_end > now,
    ).order_by(AlokoSubscription.period_end.desc()).first()
    return row is not None


def _normalise_domain(value: str) -> str:
    value = value.strip().lower()
    if not value:
        raise ValueError("Empty domain")
    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError("Only HTTP or HTTPS website URLs are allowed")
        if parsed.username or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ValueError("Enter a domain only, without paths or credentials")
    else:
        parsed = urlparse("//" + value)
        if parsed.path or parsed.query or parsed.fragment:
            raise ValueError("Enter a domain only, without paths")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host or " " in host:
        raise ValueError("Invalid domain")
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("Localhost is not allowed for production widget domains")
    return host


def _allowed_origin(config: SupportWidgetConfig, origin: str | None) -> bool:
    if not origin:
        return False
    try:
        host = _normalise_domain(origin)
        allowed = {
            _normalise_domain(item)
            for item in (config.allowed_domains or "").splitlines()
            if item.strip()
        }
        return host in allowed
    except ValueError:
        return False


def _cors(response: Response, origin: str | None):
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    response.headers["Cache-Control"] = "no-store"
    return response


def _get_config(public_id: str, db: Session):
    config = db.query(SupportWidgetConfig).filter(
        SupportWidgetConfig.public_id == public_id,
        SupportWidgetConfig.is_enabled.is_(True),
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Widget not found or disabled.")
    workspace = db.query(SupportWorkspace).filter(
        SupportWorkspace.id == config.workspace_id,
        SupportWorkspace.status == "active",
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Widget unavailable.")
    return config, workspace


@router.get("/workspaces/{workspace_id}/settings")
def get_widget_settings(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = _owned_workspace(workspace_id, user, db)
    config = db.query(SupportWidgetConfig).filter(
        SupportWidgetConfig.workspace_id == workspace.id
    ).first()

    if not config:
        config = SupportWidgetConfig(
            workspace_id=workspace.id,
            public_id=secrets.token_urlsafe(24),
            allowed_domains="",
            is_enabled=False,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    api_base = "https://aloko-1.onrender.com"
    embed_code = (
        f'<script src="{api_base}/customer-support/widget.js" '
        f'data-widget-id="{config.public_id}" defer></script>'
    )
    return {
        "success": True,
        "public_id": config.public_id,
        "allowed_domains": [
            item for item in (config.allowed_domains or "").splitlines() if item
        ],
        "is_enabled": config.is_enabled,
        "embed_code": embed_code,
        "script_url": f"{api_base}/customer-support/widget.js",
    }


@router.put("/workspaces/{workspace_id}/settings")
def update_widget_settings(
    workspace_id: int,
    data: WidgetSettings,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = _owned_workspace(workspace_id, user, db)
    config = db.query(SupportWidgetConfig).filter(
        SupportWidgetConfig.workspace_id == workspace.id
    ).first()

    if not config:
        config = SupportWidgetConfig(
            workspace_id=workspace.id,
            public_id=secrets.token_urlsafe(24),
            allowed_domains="",
            is_enabled=False,
        )
        db.add(config)
        db.flush()

    normalised = []
    for domain in data.allowed_domains:
        try:
            host = _normalise_domain(domain)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid website domain: {domain}")
        if host not in normalised:
            normalised.append(host)

    if data.is_enabled and not normalised:
        raise HTTPException(
            status_code=422,
            detail="Add at least one allowed website domain before enabling the widget.",
        )

    config.allowed_domains = "\n".join(normalised)
    config.is_enabled = data.is_enabled
    db.commit()
    db.refresh(config)

    return {
        "success": True,
        "public_id": config.public_id,
        "allowed_domains": normalised,
        "is_enabled": config.is_enabled,
    }


@router.get("/{public_id}/config")
def public_widget_config(
    public_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    config, workspace = _get_config(public_id, db)
    origin = request.headers.get("origin")
    if not _allowed_origin(config, origin):
        raise HTTPException(status_code=403, detail="This website is not allowed to use the widget.")
    response = Response(
        content=json.dumps({
            "success": True,
            "company_name": workspace.name,
            "industry": workspace.industry,
            "description": workspace.description or "",
        }),
        media_type="application/json",
    )
    return _cors(response, origin)


@router.post("/{public_id}/chat")
async def public_widget_chat(
    public_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    # The embed uses text/plain to avoid a cross-origin JSON preflight.
    # Parse and validate its JSON body explicitly.
    raw_body = await request.body()
    if len(raw_body) > 10_000:
        raise HTTPException(status_code=413, detail="Request body is too large.")

    try:
        data = WidgetChatRequest.parse_raw(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid chat request.")

    config, workspace = _get_config(public_id, db)
    origin = request.headers.get("origin")
    if not _allowed_origin(config, origin):
        raise HTTPException(status_code=403, detail="This website is not allowed to use the widget.")

    owner_id = workspace.user_id
    if not _active_subscription(owner_id, db):
        raise HTTPException(status_code=402, detail="The workspace subscription is inactive.")

    # A simple per-widget global safety cap; the DB-backed count works across workers.
    # This is not a substitute for edge/IP rate limiting on a public production service.
    recent_cutoff = datetime.now(timezone.utc).replace(microsecond=0)
    from datetime import timedelta
    recent_cutoff = recent_cutoff - timedelta(minutes=1)
    recent_count = db.query(SupportMessage).join(
        SupportConversation,
        SupportMessage.conversation_id == SupportConversation.id,
    ).filter(
        SupportConversation.workspace_id == workspace.id,
        SupportConversation.channel == "website_widget",
        SupportMessage.sender_type == "customer",
        SupportMessage.created_at >= recent_cutoff,
    ).count()
    if recent_count >= 60:
        raise HTTPException(status_code=429, detail="This support widget is busy. Please try again shortly.")

    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    conversation = None
    visitor_token = data.visitor_token

    if data.conversation_id is not None:
        # The conversation ID alone is not sufficient to access a chat.
        if not visitor_token:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        conversation = db.query(SupportConversation).filter(
            SupportConversation.id == data.conversation_id,
            SupportConversation.workspace_id == workspace.id,
            SupportConversation.channel == "website_widget",
            SupportConversation.status == "open",
            SupportConversation.customer_identifier == "web:" + visitor_token,
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")

    if conversation is None:
        # Create a private visitor token and bind it to this conversation.
        visitor_token = secrets.token_urlsafe(32)
        conversation = SupportConversation(
            workspace_id=workspace.id,
            customer_identifier="web:" + visitor_token,
            channel="website_widget",
            status="open",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    history_rows = db.query(SupportMessage).filter(
        SupportMessage.conversation_id == conversation.id
    ).order_by(SupportMessage.id.desc()).limit(10).all()
    history = [
        {"role": "assistant" if row.sender_type == "assistant" else "user",
         "content": row.content}
        for row in reversed(history_rows)
    ]

    knowledge = db.query(SupportKnowledgeItem).filter(
        SupportKnowledgeItem.workspace_id == workspace.id,
        SupportKnowledgeItem.is_active.is_(True),
    ).order_by(SupportKnowledgeItem.id.desc()).limit(50).all()
    knowledge_payload = [
        {"title": item.title, "content": item.content, "category": item.category or ""}
        for item in knowledge
    ]

    db.add(SupportMessage(
        conversation_id=conversation.id,
        sender_type="customer",
        content=message,
    ))
    db.commit()

    try:
        reply = generate_support_reply(
            company_name=workspace.name,
            industry=workspace.industry,
            description=workspace.description or "",
            knowledge_items=knowledge_payload,
            conversation_history=history,
            customer_message=message,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="The AI service could not generate a reply.")

    db.add(SupportMessage(
        conversation_id=conversation.id,
        sender_type="assistant",
        content=reply,
    ))
    db.commit()

    response = Response(
        content=json.dumps({
            "success": True,
            "conversation_id": conversation.id,
            "visitor_token": visitor_token,
            "reply": reply,
        }),
        media_type="application/json",
    )
    return _cors(response, origin)


@router.get("/widget.js")
def website_widget_script():
    script = r"""
(function () {
  var tag = document.currentScript;
  if (!tag) return;
  var widgetId = tag.getAttribute("data-widget-id");
  if (!widgetId || !/^[A-Za-z0-9_-]{20,80}$/.test(widgetId)) return;
  var apiBase = new URL(tag.src).origin;
  if (document.getElementById("aloko-support-launcher")) return;

  var style = document.createElement("style");
  style.textContent = `
    #aloko-support-launcher{position:fixed;right:22px;bottom:22px;z-index:2147483000;border:0;border-radius:28px;background:#4f46e5;color:white;padding:14px 19px;font:600 15px system-ui;box-shadow:0 8px 28px #0003;cursor:pointer}
    #aloko-support-panel{position:fixed;right:22px;bottom:82px;z-index:2147483000;width:min(360px,calc(100vw - 28px));height:min(500px,calc(100vh - 110px));background:#fff;color:#111827;border:1px solid #e5e7eb;border-radius:16px;box-shadow:0 12px 40px #0003;display:none;overflow:hidden;font:14px system-ui}
    #aloko-support-head{background:#4f46e5;color:white;padding:15px;font-weight:700}
    #aloko-support-messages{height:calc(100% - 135px);overflow:auto;padding:12px;display:flex;flex-direction:column;gap:9px}
    .aloko-support-msg{padding:10px 12px;border-radius:12px;max-width:88%;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.45}
    .aloko-support-user{align-self:flex-end;background:#e0e7ff}.aloko-support-ai{align-self:flex-start;background:#f3f4f6}
    #aloko-support-form{display:flex;gap:7px;padding:10px;border-top:1px solid #e5e7eb}
    #aloko-support-input{min-width:0;flex:1;border:1px solid #d1d5db;border-radius:9px;padding:10px;font:inherit}
    #aloko-support-send{border:0;border-radius:9px;background:#4f46e5;color:#fff;padding:0 13px;cursor:pointer}
  `;
  document.head.appendChild(style);

  var button = document.createElement("button");
  button.id = "aloko-support-launcher";
  button.type = "button";
  button.textContent = "Chat with us";

  var panel = document.createElement("section");
  panel.id = "aloko-support-panel";
  panel.setAttribute("aria-label", "Customer support chat");
  var head = document.createElement("div");
  head.id = "aloko-support-head";
  head.textContent = "Customer support";
  var messages = document.createElement("div");
  messages.id = "aloko-support-messages";
  var form = document.createElement("form");
  form.id = "aloko-support-form";
  var input = document.createElement("input");
  input.id = "aloko-support-input";
  input.maxLength = 2000;
  input.placeholder = "Type your question...";
  input.setAttribute("aria-label", "Your message");
  input.required = true;
  var send = document.createElement("button");
  send.id = "aloko-support-send";
  send.type = "submit";
  send.textContent = "Send";
  form.append(input, send);
  panel.append(head, messages, form);
  document.body.append(button, panel);

  var conversationId = null;
  var visitorToken = null;
  var busy = false;

  function addMessage(text, who) {
    var node = document.createElement("div");
    node.className = "aloko-support-msg " + (who === "user" ? "aloko-support-user" : "aloko-support-ai");
    node.textContent = text;
    messages.appendChild(node);
    messages.scrollTop = messages.scrollHeight;
  }

  button.addEventListener("click", function () {
    var open = panel.style.display === "block";
    panel.style.display = open ? "none" : "block";
    if (!open) input.focus();
  });

  fetch(apiBase + "/customer-support/widget/" + encodeURIComponent(widgetId) + "/config")
    .then(function (r) { if (!r.ok) throw new Error("Widget unavailable"); return r.json(); })
    .then(function (cfg) {
      head.textContent = (cfg.company_name || "Customer support") + " ? AI assistant";
      addMessage("Hello! How can we help you today?", "ai");
    })
    .catch(function () {
      button.disabled = true;
      button.textContent = "Chat unavailable";
    });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    var message = input.value.trim();
    if (!message || busy) return;
    busy = true;
    send.disabled = true;
    input.disabled = true;
    addMessage(message, "user");
    input.value = "";
    try {
      var response = await fetch(apiBase + "/customer-support/widget/" + encodeURIComponent(widgetId) + "/chat", {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=UTF-8" },
        body: JSON.stringify({
          message: message,
          conversation_id: conversationId,
          visitor_token: visitorToken
        })
      });
      var result = await response.json().catch(function () { return {}; });
      if (!response.ok) throw new Error(result.detail || "Unable to send your message.");
      conversationId = result.conversation_id;
      visitorToken = result.visitor_token || visitorToken;
      addMessage(result.reply || "Sorry, I couldn't generate a reply.", "ai");
    } catch (error) {
      addMessage(error.message || "Connection error. Please try again.", "ai");
    } finally {
      busy = false;
      send.disabled = false;
      input.disabled = false;
      input.focus();
    }
  });
})();
"""
    return Response(content=script, media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=300"})
