import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User

from app.business_ai.models import (
    BusinessWorkspace,
    BusinessDataset,
    BusinessMemory,
    BusinessReport,
)

from app.business_ai.services.report_engine import (
    build_business_report,
)


router = APIRouter(
    prefix="/business/reports",
    tags=["Business AI - Reports"],
)


class ReportCreateRequest(BaseModel):
    workspace_id: int = Field(..., gt=0)

    title: str = Field(
        default="Business Analysis Report",
        min_length=1,
        max_length=255,
    )

    question: str | None = Field(
        default=None,
        max_length=2000,
    )

    memory_id: int | None = Field(
        default=None,
        gt=0,
    )


@router.post("/generate")
def generate_business_report(
    data: ReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. VERIFY WORKSPACE
    workspace = (
        db.query(BusinessWorkspace)
        .filter(
            BusinessWorkspace.id == data.workspace_id,
            BusinessWorkspace.user_id == current_user.id,
            BusinessWorkspace.status == "active",
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Business workspace not found.",
        )

    # 2. LOAD DATASETS
    datasets = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.workspace_id == workspace.id,
            BusinessDataset.user_id == current_user.id,
            BusinessDataset.status == "ready",
        )
        .all()
    )

    if not datasets:
        raise HTTPException(
            status_code=400,
            detail="No ready datasets are available.",
        )

    dataset_info = []

    for dataset in datasets:
        dataset_info.append(
            {
                "dataset_id": dataset.id,
                "dataset_name": dataset.name,
                "source_type": dataset.source_type,
                "row_count": dataset.row_count,
            }
        )

    # 3. LOAD SOURCE MEMORY
    memory = None

    if data.memory_id:
        memory = (
            db.query(BusinessMemory)
            .filter(
                BusinessMemory.id == data.memory_id,
                BusinessMemory.workspace_id == workspace.id,
                BusinessMemory.user_id == current_user.id,
            )
            .first()
        )

        if not memory:
            raise HTTPException(
                status_code=404,
                detail="Business analysis memory not found.",
            )
    else:
        memory = (
            db.query(BusinessMemory)
            .filter(
                BusinessMemory.workspace_id == workspace.id,
                BusinessMemory.user_id == current_user.id,
            )
            .order_by(
                BusinessMemory.created_at.desc()
            )
            .first()
        )

    if not memory:
        raise HTTPException(
            status_code=400,
            detail=(
                "No completed business analysis is available. "
                "Ask Aloko a business question first."
            ),
        )

    # 4. LOAD STORED RESULT
    try:
        summary = json.loads(
            memory.result_summary or "{}"
        )
    except json.JSONDecodeError:
        summary = {}

    # 5. BUILD REPORT
    report = build_business_report(
        title=data.title,
        question=data.question or memory.question,
        datasets=dataset_info,
        summary=summary,
        answer=memory.ai_answer or "",
        key_findings=[],
        caveats=[],
        metrics=[],
        selected_metrics=[],
        chart={
            "type": memory.chart_type or "table",
            "data": summary.get("rows", []),
            "options": {},
        },
        chart_decision={
            "chart_type": memory.chart_type or "table",
        },
    )

    # 6. SAVE REPORT
    report_record = BusinessReport(
        workspace_id=workspace.id,
        user_id=current_user.id,
        title=data.title,
        report_type="business_analysis",
        question=data.question or memory.question,
        source_memory_id=memory.id,
        content_json=json.dumps(
            report,
            default=str,
        ),
        status="ready",
    )

    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    return {
        "success": True,
        "report": {
            "id": report_record.id,
            "title": report_record.title,
            "report_type": report_record.report_type,
            "question": report_record.question,
            "source_memory_id": report_record.source_memory_id,
            "status": report_record.status,
            "created_at": report_record.created_at,
            "content": report,
        },
    }


@router.get("")
def list_business_reports(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = (
        db.query(BusinessWorkspace)
        .filter(
            BusinessWorkspace.id == workspace_id,
            BusinessWorkspace.user_id == current_user.id,
            BusinessWorkspace.status == "active",
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Business workspace not found.",
        )

    reports = (
        db.query(BusinessReport)
        .filter(
            BusinessReport.workspace_id == workspace.id,
            BusinessReport.user_id == current_user.id,
        )
        .order_by(
            BusinessReport.created_at.desc()
        )
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
            }
            for report in reports
        ],
    }


@router.get("/{report_id}")
def get_business_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(BusinessReport)
        .filter(
            BusinessReport.id == report_id,
            BusinessReport.user_id == current_user.id,
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Business report not found.",
        )

    try:
        content = json.loads(
            report.content_json
        )
    except json.JSONDecodeError:
        content = {}

    return {
        "success": True,
        "report": {
            "id": report.id,
            "title": report.title,
            "report_type": report.report_type,
            "question": report.question,
            "source_memory_id": report.source_memory_id,
            "status": report.status,
            "created_at": report.created_at,
            "content": content,
        },
    }