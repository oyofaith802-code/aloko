from datetime import datetime, timezone
import csv
import io
import re
import uuid
from pathlib import Path
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User
from app.customer_support.models import (
    SupportWorkspace,
    SupportKnowledgeItem,
    SupportConversation,
    SupportMessage,
    SupportKnowledgeImportDraft,
)
from app.customer_support.agent import generate_support_reply
from app.customer_support.demo import is_demo_workspace
from app.billing.models import AlokoSubscription, CustomerSupportUsage


router = APIRouter(
    prefix="/customer-support",
    tags=["Aloko Customer Support"],
)


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry: str = Field(default="other", max_length=100)
    description: str | None = Field(default=None, max_length=5000)


class KnowledgeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=20000)
    category: str | None = Field(default=None, max_length=100)


class TestChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: int | None = None


def get_owned_workspace(
    workspace_id: int,
    user: User,
    db: Session,
) -> SupportWorkspace:
    workspace = (
        db.query(SupportWorkspace)
        .filter(
            SupportWorkspace.id == workspace_id,
            SupportWorkspace.user_id == user.id,
            SupportWorkspace.status == "active",
        )
        .first()
    )
    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Customer support workspace not found.",
        )
    return workspace


@router.post("/workspaces")
def create_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Company name is required.")

    workspace = SupportWorkspace(
        user_id=user.id,
        name=name,
        industry=data.industry.strip() or "other",
        description=data.description,
        status="active",
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return {
        "success": True,
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "industry": workspace.industry,
            "description": workspace.description,
            "status": workspace.status,
            "created_at": workspace.created_at,
        },
    }


@router.get("/workspaces")
def list_workspaces(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = (
        db.query(SupportWorkspace)
        .filter(SupportWorkspace.user_id == user.id)
        .order_by(SupportWorkspace.created_at.desc())
        .all()
    )
    return {
        "success": True,
        "workspaces": [
            {
                "id": item.id,
                "name": item.name,
                "industry": item.industry,
                "description": item.description,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in items
        ],
    }


@router.get("/workspaces/{workspace_id}")
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = get_owned_workspace(workspace_id, user, db)
    return {
        "success": True,
        "workspace": {
            "id": item.id,
            "name": item.name,
            "industry": item.industry,
            "description": item.description,
            "status": item.status,
            "created_at": item.created_at,
        },
    }


@router.post("/workspaces/{workspace_id}/knowledge")
def add_knowledge(
    workspace_id: int,
    data: KnowledgeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)

    title = data.title.strip()
    content = data.content.strip()
    if not title or not content:
        raise HTTPException(
            status_code=422,
            detail="Knowledge title and content cannot be empty.",
        )

    item = SupportKnowledgeItem(
        workspace_id=workspace.id,
        title=title,
        content=content,
        category=data.category,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "success": True,
        "knowledge": {
            "id": item.id,
            "workspace_id": item.workspace_id,
            "title": item.title,
            "content": item.content,
            "category": item.category,
            "is_active": item.is_active,
        },
    }


@router.get("/workspaces/{workspace_id}/knowledge")
def list_knowledge(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)
    items = (
        db.query(SupportKnowledgeItem)
        .filter(
            SupportKnowledgeItem.workspace_id == workspace.id,
            SupportKnowledgeItem.is_active.is_(True),
        )
        .order_by(SupportKnowledgeItem.id.desc())
        .all()
    )
    return {
        "success": True,
        "knowledge": [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category": item.category,
                "created_at": item.created_at,
            }
            for item in items
        ],
    }


@router.delete("/workspaces/{workspace_id}/knowledge/{knowledge_id}")
def delete_knowledge(
    workspace_id: int,
    knowledge_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)
    item = (
        db.query(SupportKnowledgeItem)
        .filter(
            SupportKnowledgeItem.id == knowledge_id,
            SupportKnowledgeItem.workspace_id == workspace.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found.")

    item.is_active = False
    db.commit()
    return {"success": True, "message": "Knowledge item deactivated."}


@router.post("/workspaces/{workspace_id}/test-chat")
def test_chat(
    workspace_id: int,
    data: TestChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)
    customer_message = data.message.strip()
    if not customer_message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    conversation = None
    if data.conversation_id is not None:
        conversation = (
            db.query(SupportConversation)
            .filter(
                SupportConversation.id == data.conversation_id,
                SupportConversation.workspace_id == workspace.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found in this workspace.",
            )
        if conversation.status != "open":
            raise HTTPException(
                status_code=409,
                detail="This conversation is not open for AI replies.",
            )

    if conversation is None:
        conversation = SupportConversation(
            workspace_id=workspace.id,
            channel="web_test",
            status="open",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    if not is_demo_workspace(workspace.id):
        # Paid access is granted only by a verified, unexpired subscription.
        now = datetime.now(timezone.utc)
        active_subscription = (
            db.query(AlokoSubscription)
            .filter(
                AlokoSubscription.user_id == user.id,
                AlokoSubscription.product == "customer_support",
                AlokoSubscription.status == "active",
                AlokoSubscription.period_end > now,
            )
            .order_by(AlokoSubscription.period_end.desc())
            .first()
        )

        # Subscribers can chat without consuming their free-test allowance.
        if not active_subscription:
            usage = (
                db.query(CustomerSupportUsage)
                .filter(CustomerSupportUsage.user_id == user.id)
                .with_for_update()
                .first()
            )

            if usage is None:
                usage = CustomerSupportUsage(user_id=user.id, free_test_used=False)
                db.add(usage)
                try:
                    db.commit()
                except IntegrityError:
                    # Another request may have created the row concurrently.
                    db.rollback()

                usage = (
                    db.query(CustomerSupportUsage)
                    .filter(CustomerSupportUsage.user_id == user.id)
                    .with_for_update()
                    .first()
                )

            test_message_count = (
                db.query(SupportMessage)
                .join(
                    SupportConversation,
                    SupportMessage.conversation_id == SupportConversation.id,
                )
                .join(
                    SupportWorkspace,
                    SupportConversation.workspace_id == SupportWorkspace.id,
                )
                .filter(
                    SupportWorkspace.user_id == user.id,
                    SupportConversation.channel.in_(["web_test", "website_widget"]),
                    SupportMessage.sender_type == "customer",
                )
                .count()
            )
            # Preserve the old one-free-test flag for accounts that used the
            # previous allowance before message history was available.
            if usage is not None and usage.free_test_used:
                test_message_count = max(test_message_count, 1)

            if usage is None or test_message_count >= 2:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": "subscription_required",
                        "message": "Your 2 free AI test messages have been used. Subscribe to Customer Support AI to continue.",
                        "prices": {"NGN": 20000},
                    },
                )

            # Commit the allowance before generating a reply so parallel requests
            # cannot both use the same free test.
            usage.free_test_used = True
            db.commit()

    history = (
        db.query(SupportMessage)
        .filter(SupportMessage.conversation_id == conversation.id)
        .order_by(SupportMessage.id.desc())
        .limit(10)
        .all()
    )
    history.reverse()

    knowledge = (
        db.query(SupportKnowledgeItem)
        .filter(
            SupportKnowledgeItem.workspace_id == workspace.id,
            SupportKnowledgeItem.is_active.is_(True),
        )
        .order_by(SupportKnowledgeItem.id.asc())
        .limit(50)
        .all()
    )

    db.add(
        SupportMessage(
            conversation_id=conversation.id,
            sender_type="customer",
            content=customer_message,
        )
    )
    db.commit()

    try:
        reply = generate_support_reply(
            company_name=workspace.name,
            industry=workspace.industry,
            description=workspace.description or "",
            knowledge_items=knowledge,
            conversation_history=history,
            customer_message=customer_message,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The AI service could not generate a reply. Check the backend logs and Groq configuration.",
        )

    db.add(
        SupportMessage(
            conversation_id=conversation.id,
            sender_type="assistant",
            content=reply,
        )
    )
    db.commit()

    return {
        "success": True,
        "conversation_id": conversation.id,
        "reply": reply,
        "channel": conversation.channel,
        "note": "Test chat only; no WhatsApp message has been sent.",
    }


@router.get("/workspaces/{workspace_id}/conversations")
def list_conversations(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)
    items = (
        db.query(SupportConversation)
        .filter(SupportConversation.workspace_id == workspace.id)
        .order_by(SupportConversation.created_at.desc())
        .limit(100)
        .all()
    )
    return {
        "success": True,
        "conversations": [
            {
                "id": item.id,
                "channel": item.channel,
                "status": item.status,
                "human_requested": item.human_requested,
                "customer_identifier": item.customer_identifier,
                "created_at": item.created_at,
            }
            for item in items
        ],
    }


@router.get("/workspaces/{workspace_id}/conversations/{conversation_id}/messages")
def list_messages(
    workspace_id: int,
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)
    conversation = (
        db.query(SupportConversation)
        .filter(
            SupportConversation.id == conversation_id,
            SupportConversation.workspace_id == workspace.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    items = (
        db.query(SupportMessage)
        .filter(SupportMessage.conversation_id == conversation.id)
        .order_by(SupportMessage.id.asc())
        .all()
    )
    return {
        "success": True,
        "messages": [
            {
                "id": item.id,
                "sender_type": item.sender_type,
                "content": item.content,
                "created_at": item.created_at,
            }
            for item in items
        ],
    }


@router.post("/workspaces/{workspace_id}/conversations/{conversation_id}/handoff")
def request_handoff(
    workspace_id: int,
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)
    conversation = (
        db.query(SupportConversation)
        .filter(
            SupportConversation.id == conversation_id,
            SupportConversation.workspace_id == workspace.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    conversation.human_requested = True
    conversation.status = "waiting_for_human"
    db.commit()

    return {
        "success": True,
        "conversation_id": conversation.id,
        "status": conversation.status,
        "message": "Handoff recorded. A human agent must still respond manually.",
    }


# ------------------------------------------------------------
# AI KNOWLEDGE IMPORT
# Extracted entries remain drafts until explicitly approved.
# ------------------------------------------------------------

MAX_KNOWLEDGE_IMPORT_BYTES = 8 * 1024 * 1024
MAX_KNOWLEDGE_IMPORT_DRAFTS = 80
ALLOWED_KNOWLEDGE_IMPORT_EXTENSIONS = {
    ".pdf", ".docx", ".txt", ".csv", ".xlsx"
}


def _knowledge_category(text: str) -> str:
    value = text.lower()

    rules = [
        ("pricing", ("price", "pricing", "cost", "?", "$", "naira", "discount")),
        ("products", ("product", "model", "specification", "features", "stock")),
        ("delivery", ("delivery", "deliver", "delivered", "shipping", "shipment", "dispatch", "pickup", "tracking")),
        ("returns", ("return", "refund", "exchange", "replacement")),
        ("policies", ("policy", "terms", "privacy", "warranty")),
        ("faqs", ("faq", "frequently asked", "question", "answer")),
    ]

    for category, keywords in rules:
        if any(keyword in value for keyword in keywords):
            return category

    return "general"


def _make_import_entries(filename: str, raw: bytes):
    extension = Path(filename).suffix.lower()
    entries = []

    if extension == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))

        if len(reader.pages) > 100:
            raise HTTPException(
                status_code=413,
                detail="PDF imports are limited to 100 pages.",
            )

        text = "\n".join(page.extract_text() or "" for page in reader.pages)

    elif extension == ".docx":
        from docx import Document

        document = Document(io.BytesIO(raw))
        parts = [paragraph.text for paragraph in document.paragraphs]

        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))

        text = "\n".join(parts)

    elif extension == ".txt":
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

    elif extension == ".csv":
        decoded = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))

        for index, row in enumerate(reader, start=1):
            content = "\n".join(
                f"{str(key).strip()}: {str(value).strip()}"
                for key, value in row.items()
                if key and value is not None and str(value).strip()
            )

            if content:
                entries.append({
                    "title": f"Imported record {index}",
                    "content": content[:20000],
                    "category": _knowledge_category(content),
                })

            if len(entries) >= MAX_KNOWLEDGE_IMPORT_DRAFTS:
                break

        return entries

    elif extension == ".xlsx":
        import pandas as pd

        workbook = pd.ExcelFile(io.BytesIO(raw))

        for sheet_name in workbook.sheet_names[:10]:
            frame = pd.read_excel(
                workbook,
                sheet_name=sheet_name,
            ).fillna("")

            for index, row in frame.head(500).iterrows():
                content = "\n".join(
                    f"{str(key).strip()}: {str(value).strip()}"
                    for key, value in row.items()
                    if str(value).strip()
                )

                if content:
                    entries.append({
                        "title": f"{sheet_name[:80]} ? record {index + 1}",
                        "content": content[:20000],
                        "category": _knowledge_category(content),
                    })

                if len(entries) >= MAX_KNOWLEDGE_IMPORT_DRAFTS:
                    return entries

        return entries

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported document type.",
        )

    sections = [
        part.strip()
        for part in re.split(r"\n\s*\n+", text)
        if part.strip()
    ]

    if not sections and text.strip():
        sections = [text.strip()]

    for index, section in enumerate(
        sections[:MAX_KNOWLEDGE_IMPORT_DRAFTS],
        start=1,
    ):
        section = section[:20000]
        first_line = next(
            (line.strip() for line in section.splitlines() if line.strip()),
            "",
        )

        entries.append({
            "title": first_line[:255] or f"Imported information {index}",
            "content": section,
            "category": _knowledge_category(section),
        })

    return entries


class KnowledgeImportReview(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=20000)
    category: str | None = Field(default="general", max_length=100)


@router.post("/workspaces/{workspace_id}/knowledge-imports")
async def upload_knowledge_import(
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)

    filename = Path(file.filename or "").name

    if Path(filename).suffix.lower() not in ALLOWED_KNOWLEDGE_IMPORT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Upload a PDF, DOCX, TXT, CSV, or XLSX file.",
        )

    raw = await file.read(MAX_KNOWLEDGE_IMPORT_BYTES + 1)
    await file.close()

    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(raw) > MAX_KNOWLEDGE_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail="Maximum upload size is 8 MB.")

    try:
        entries = _make_import_entries(filename, raw)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="The document could not be read. Check that it is a valid supported file.",
        )

    if not entries:
        raise HTTPException(
            status_code=422,
            detail="No readable information was found. Scanned PDFs require OCR.",
        )

    batch_id = str(uuid.uuid4())
    drafts = []

    for entry in entries:
        draft = SupportKnowledgeImportDraft(
            workspace_id=workspace.id,
            import_batch_id=batch_id,
            source_filename=filename[:255],
            title=entry["title"][:255],
            content=entry["content"][:20000],
            category=entry["category"],
            status="pending",
        )
        db.add(draft)
        drafts.append(draft)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save imported drafts.",
        )

    for draft in drafts:
        db.refresh(draft)

    return {
        "success": True,
        "batch_id": batch_id,
        "filename": filename,
        "draft_count": len(drafts),
        "message": "Entries extracted. Review and approve them before they enter your live knowledge base.",
        "drafts": [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category": item.category,
                "status": item.status,
                "source_filename": item.source_filename,
            }
            for item in drafts
        ],
    }


@router.get("/workspaces/{workspace_id}/knowledge-imports")
def list_knowledge_import_drafts(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)

    drafts = (
        db.query(SupportKnowledgeImportDraft)
        .filter(SupportKnowledgeImportDraft.workspace_id == workspace.id)
        .order_by(
            SupportKnowledgeImportDraft.created_at.desc(),
            SupportKnowledgeImportDraft.id.desc(),
        )
        .limit(500)
        .all()
    )

    return {
        "success": True,
        "drafts": [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "category": item.category,
                "status": item.status,
                "source_filename": item.source_filename,
                "created_at": item.created_at,
            }
            for item in drafts
        ],
    }


@router.patch("/workspaces/{workspace_id}/knowledge-imports/{draft_id}")
def update_knowledge_import_draft(
    workspace_id: int,
    draft_id: int,
    data: KnowledgeImportReview,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)

    draft = (
        db.query(SupportKnowledgeImportDraft)
        .filter(
            SupportKnowledgeImportDraft.id == draft_id,
            SupportKnowledgeImportDraft.workspace_id == workspace.id,
            SupportKnowledgeImportDraft.status == "pending",
        )
        .first()
    )

    if not draft:
        raise HTTPException(status_code=404, detail="Pending import draft not found.")

    draft.title = data.title.strip()
    draft.content = data.content.strip()
    draft.category = (data.category or "general").strip() or "general"

    if not draft.title or not draft.content:
        raise HTTPException(status_code=422, detail="Title and content cannot be empty.")

    db.commit()

    return {"success": True, "message": "Draft updated."}


@router.post("/workspaces/{workspace_id}/knowledge-imports/{draft_id}/approve")
def approve_knowledge_import_draft(
    workspace_id: int,
    draft_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)

    draft = (
        db.query(SupportKnowledgeImportDraft)
        .filter(
            SupportKnowledgeImportDraft.id == draft_id,
            SupportKnowledgeImportDraft.workspace_id == workspace.id,
            SupportKnowledgeImportDraft.status == "pending",
        )
        .with_for_update()
        .first()
    )

    if not draft:
        raise HTTPException(status_code=404, detail="Pending import draft not found.")

    live_item = SupportKnowledgeItem(
        workspace_id=workspace.id,
        title=draft.title,
        content=draft.content,
        category=draft.category,
        is_active=True,
    )

    db.add(live_item)
    draft.status = "approved"
    draft.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(live_item)

    return {
        "success": True,
        "message": "Draft approved and added to live knowledge.",
        "knowledge_id": live_item.id,
    }


@router.post("/workspaces/{workspace_id}/knowledge-imports/{draft_id}/reject")
def reject_knowledge_import_draft(
    workspace_id: int,
    draft_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workspace = get_owned_workspace(workspace_id, user, db)

    draft = (
        db.query(SupportKnowledgeImportDraft)
        .filter(
            SupportKnowledgeImportDraft.id == draft_id,
            SupportKnowledgeImportDraft.workspace_id == workspace.id,
            SupportKnowledgeImportDraft.status == "pending",
        )
        .first()
    )

    if not draft:
        raise HTTPException(status_code=404, detail="Pending import draft not found.")

    draft.status = "rejected"
    draft.reviewed_at = datetime.now(timezone.utc)

    db.commit()

    return {"success": True, "message": "Draft rejected."}
