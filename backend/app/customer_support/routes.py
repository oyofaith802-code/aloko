from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter, Depends, HTTPException
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
)
from app.customer_support.agent import generate_support_reply
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
