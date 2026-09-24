from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User

from app.business_ai.models.workspace import BusinessWorkspace
from app.business_ai.models.dataset import BusinessDataset
from app.business_ai.models.business_memory import BusinessMemory
from app.business_ai.models.business_report import BusinessReport
from app.business_ai.services.dataset_cleanup import delete_dataset_storage


router = APIRouter(
    prefix="/business",
    tags=["Business AI"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class AskBusinessRequest(BaseModel):
    workspace_id: int
    question: str = Field(..., min_length=1, max_length=5000)


# ============================================================
# WORKSPACES
# ============================================================

@router.get("/workspaces")
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspaces = (
        db.query(BusinessWorkspace)
        .filter(BusinessWorkspace.user_id == current_user.id)
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
                "updated_at": workspace.updated_at,
            }
            for workspace in workspaces
        ],
    }


@router.post("/workspaces")
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = BusinessWorkspace(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description,
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
        },
    }


@router.get("/workspaces/{workspace_id}")
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

    dataset_count = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.workspace_id == workspace.id,
            BusinessDataset.user_id == current_user.id,
        )
        .count()
    )

    memory_count = (
        db.query(BusinessMemory)
        .filter(
            BusinessMemory.workspace_id == workspace.id,
            BusinessMemory.user_id == current_user.id,
        )
        .count()
    )

    report_count = (
        db.query(BusinessReport)
        .filter(
            BusinessReport.workspace_id == workspace.id,
            BusinessReport.user_id == current_user.id,
        )
        .count()
    )

    return {
        "success": True,
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "status": workspace.status,
            "dataset_count": dataset_count,
            "memory_count": memory_count,
            "report_count": report_count,
            "created_at": workspace.created_at,
            "updated_at": workspace.updated_at,
        },
    }


# ============================================================
# DATASETS
# ============================================================

@router.get("/workspaces/{workspace_id}/datasets")
def list_business_datasets(
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

    datasets = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.workspace_id == workspace_id,
            BusinessDataset.user_id == current_user.id,
        )
        .order_by(BusinessDataset.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "datasets": [
            {
                "id": dataset.id,
                "name": dataset.name,
                "original_filename": dataset.original_filename,
                "source_type": dataset.source_type,
                "table_name": dataset.table_name,
                "row_count": dataset.row_count,
                "schema_json": dataset.schema_json,
                "profile_json": dataset.profile_json,
                "status": dataset.status,
                "created_at": dataset.created_at,
                "updated_at": dataset.updated_at,
            }
            for dataset in datasets
        ],
    }


@router.get("/workspaces/{workspace_id}/datasets/{dataset_id}")
def get_business_dataset(
    workspace_id: int,
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.id == dataset_id,
            BusinessDataset.workspace_id == workspace_id,
            BusinessDataset.user_id == current_user.id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    return {
        "success": True,
        "dataset": {
            "id": dataset.id,
            "name": dataset.name,
            "original_filename": dataset.original_filename,
            "source_type": dataset.source_type,
            "table_name": dataset.table_name,
            "row_count": dataset.row_count,
            "schema_json": dataset.schema_json,
            "profile_json": dataset.profile_json,
            "status": dataset.status,
            "created_at": dataset.created_at,
            "updated_at": dataset.updated_at,
        },
    }


# ============================================================
# BUSINESS MEMORY / HISTORY
# ============================================================

@router.delete("/workspaces/{workspace_id}/datasets/{dataset_id}")
def delete_business_dataset(
    workspace_id: int,
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.id == dataset_id,
            BusinessDataset.workspace_id == workspace_id,
            BusinessDataset.user_id == current_user.id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    storage_path = dataset.storage_path
    table_name = dataset.table_name

    try:
        delete_dataset_storage(storage_path, table_name)
        db.delete(dataset)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete dataset: {exc}",
        )

    return {
        "success": True,
        "message": "Dataset deleted successfully.",
        "dataset_id": dataset_id,
    }

@router.get("/workspaces/{workspace_id}/memory")
def get_business_memory(
    workspace_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 100))

    memories = (
        db.query(BusinessMemory)
        .filter(
            BusinessMemory.workspace_id == workspace_id,
            BusinessMemory.user_id == current_user.id,
        )
        .order_by(BusinessMemory.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "memory": [
            {
                "id": item.id,
                "question": item.question,
                "sql_query": item.sql_query,
                "result_summary": item.result_summary,
                "ai_answer": item.ai_answer,
                "chart_type": item.chart_type,
                "created_at": item.created_at,
            }
            for item in memories
        ],
    }


# ============================================================
# BUSINESS REPORTS
# ============================================================

@router.get("/workspaces/{workspace_id}/reports")
def list_business_reports(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = (
        db.query(BusinessReport)
        .filter(
            BusinessReport.workspace_id == workspace_id,
            BusinessReport.user_id == current_user.id,
        )
        .order_by(BusinessReport.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "reports": [
            {
                "id": report.id,
                "title": report.title,
                "report_type": report.report_type,
                "question": report.question,
                "source_memory_id": report.source_memory_id,
                "status": report.status,
                "created_at": report.created_at,
                "updated_at": report.updated_at,
            }
            for report in reports
        ],
    }


@router.get("/workspaces/{workspace_id}/reports/{report_id}")
def get_business_report(
    workspace_id: int,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(BusinessReport)
        .filter(
            BusinessReport.id == report_id,
            BusinessReport.workspace_id == workspace_id,
            BusinessReport.user_id == current_user.id,
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Business report not found.",
        )

    return {
        "success": True,
        "report": {
            "id": report.id,
            "title": report.title,
            "report_type": report.report_type,
            "question": report.question,
            "source_memory_id": report.source_memory_id,
            "content_json": report.content_json,
            "file_path": report.file_path,
            "status": report.status,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
        },
    }


# ============================================================
# BUSINESS DASHBOARD
# ============================================================

@router.get("/workspaces/{workspace_id}/dashboard")
def business_dashboard(
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

    datasets = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.workspace_id == workspace_id,
            BusinessDataset.user_id == current_user.id,
        )
        .all()
    )

    memory_count = (
        db.query(BusinessMemory)
        .filter(
            BusinessMemory.workspace_id == workspace_id,
            BusinessMemory.user_id == current_user.id,
        )
        .count()
    )

    report_count = (
        db.query(BusinessReport)
        .filter(
            BusinessReport.workspace_id == workspace_id,
            BusinessReport.user_id == current_user.id,
        )
        .count()
    )

    total_rows = sum(
        int(dataset.row_count or 0)
        for dataset in datasets
    )

    return {
        "success": True,
        "dashboard": {
            "workspace": {
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
            },
            "statistics": {
                "datasets": len(datasets),
                "total_rows": total_rows,
                "questions_answered": memory_count,
                "reports": report_count,
            },
            "datasets": [
                {
                    "id": dataset.id,
                    "name": dataset.name,
                    "source_type": dataset.source_type,
                    "row_count": dataset.row_count,
                    "status": dataset.status,
                }
                for dataset in datasets
            ],
        },
    }

