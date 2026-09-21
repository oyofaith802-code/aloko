from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User

from app.business_ai.models import BusinessWorkspace


router = APIRouter(
    prefix="/business/workspaces",
    tags=["Business AI - Workspaces"],
)


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


@router.post("")
def create_workspace(
    data: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = BusinessWorkspace(
        user_id=current_user.id,
        name=data.name.strip(),
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
            "description": workspace.description,
            "status": workspace.status,
            "created_at": workspace.created_at,
        },
    }


@router.get("")
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces = (
        db.query(BusinessWorkspace)
        .filter(
            BusinessWorkspace.user_id == current_user.id
        )
        .order_by(BusinessWorkspace.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "workspaces": [
            {
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "status": workspace.status,
                "created_at": workspace.created_at,
            }
            for workspace in workspaces
        ],
    }


@router.get("/{workspace_id}")
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = (
        db.query(BusinessWorkspace)
        .filter(
            BusinessWorkspace.id == workspace_id,
            BusinessWorkspace.user_id == current_user.id,
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Business workspace not found.",
        )

    return {
        "success": True,
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "status": workspace.status,
            "created_at": workspace.created_at,
        },
    }