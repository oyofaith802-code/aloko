import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User

from app.business_ai.models import (
    BusinessWorkspace,
    BusinessDataset,
    BusinessMemory,
)

from app.business_ai.services.sql_agent import generate_sql
from app.business_ai.services.sql_engine import run_safe_query
from app.business_ai.services.answer_agent import (
    generate_business_answer,
)
from app.business_ai.services.metrics_engine import (
    analyze_business_metrics,
)
from app.business_ai.services.chart_engine import (
    analyze_chart,
)

router = APIRouter(
    prefix="/business/analysis",
    tags=["Business AI - Analysis"],
)


class AnalysisRequest(BaseModel):
    workspace_id: int = Field(..., gt=0)
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


@router.post("/ask")
def ask_business_question(
    data: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ========================================================
    # 1. LOAD WORKSPACE
    # ========================================================

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

    # ========================================================
    # 2. LOAD DATASETS
    # ========================================================

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
            detail="No ready datasets are available in this workspace.",
        )

    schemas = []
    allowed_tables = []

    for dataset in datasets:
        if not dataset.table_name:
            continue

        try:
            schema = json.loads(
                dataset.schema_json or "{}"
            )
        except json.JSONDecodeError:
            schema = {}

        schemas.append(
            {
                "dataset_id": dataset.id,
                "dataset_name": dataset.name,
                "table_name": dataset.table_name,
                "schema": schema,
            }
        )

        allowed_tables.append(dataset.table_name)

    if not schemas:
        raise HTTPException(
            status_code=400,
            detail="No usable dataset schemas were found.",
        )

    # ========================================================
    # 3. GENERATE SQL
    # ========================================================

    try:
        sql_result = generate_sql(
            question=data.question,
            schemas=schemas,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"SQL generation failed: {str(exc)}",
        )

    # ========================================================
    # 4. CHECK ANSWERABILITY
    # ========================================================

    if not sql_result.get("answerable"):
        reason = sql_result.get(
            "reason",
            "This question cannot be answered from the available datasets.",
        )

        memory = BusinessMemory(
            workspace_id=workspace.id,
            user_id=current_user.id,
            question=data.question,
            sql_query=None,
            result_summary=None,
            ai_answer=reason,
            chart_type=None,
        )

        db.add(memory)
        db.commit()
        db.refresh(memory)

        return {
            "success": True,
            "answerable": False,
            "question": data.question,
            "reason": reason,
            "answer": reason,
            "key_findings": [],
            "caveats": [],
            "metrics": [],
            "selected_metrics": [],
            "chart": {
                "type": "none",
            },
            "memory_id": memory.id,
        }

    # ========================================================
    # 5. GET GENERATED SQL
    # ========================================================

    generated_sql = sql_result.get("sql")

    if not generated_sql:
        raise HTTPException(
            status_code=500,
            detail="AI returned no SQL query.",
        )

    # ========================================================
    # 6. SAFE SQL EXECUTION
    # ========================================================

    try:
        query_result = run_safe_query(
            sql=generated_sql,
            allowed_tables=allowed_tables,
            max_rows=500,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unsafe or invalid SQL: {str(exc)}",
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    summary = query_result.get(
        "summary",
        {},
    )

    rows = query_result.get(
        "rows",
        [],
    )

    executed_sql = query_result.get(
        "sql",
        generated_sql,
    )

    # ========================================================
    # 7. BUSINESS METRICS
    # ========================================================

    all_metrics = []

    selected_metrics = []

    for schema_item in schemas:
        try:
            metric_result = analyze_business_metrics(
                schema=schema_item.get(
                    "schema",
                    {},
                ),
                question=data.question,
            )

            all_metrics.extend(
                metric_result.get(
                    "metrics",
                    [],
                )
            )

            selected_metrics.extend(
                metric_result.get(
                    "selected_metrics",
                    [],
                )
            )

        except Exception:
            continue

    # Remove duplicate metrics.

    unique_metrics = {}

    for metric in all_metrics:
        name = metric.get("name")

        if not name:
            continue

        existing = unique_metrics.get(name)

        if (
            existing is None
            or metric.get("confidence", 0)
            > existing.get("confidence", 0)
        ):
            unique_metrics[name] = metric

    all_metrics = list(
        unique_metrics.values()
    )

    unique_selected_metrics = {}

    for metric in selected_metrics:
        name = metric.get("name")

        if not name:
            continue

        existing = unique_selected_metrics.get(name)

        if (
            existing is None
            or metric.get("confidence", 0)
            > existing.get("confidence", 0)
        ):
            unique_selected_metrics[name] = metric

    selected_metrics = list(
        unique_selected_metrics.values()
    )

    # ========================================================
    # 8. BUSINESS ANSWER AI
    # ========================================================

    try:
        business_answer = generate_business_answer(
            question=data.question,
            sql=executed_sql,
            summary=summary,
        )

    except Exception as exc:
        business_answer = {
            "answer": (
                "The analysis was completed successfully, "
                "but Aloko could not generate the natural-language "
                "business explanation."
            ),
            "key_findings": [],
            "caveats": [
                "Business answer generation failed."
            ],
        }

    answer = business_answer.get(
        "answer",
        "Analysis completed successfully.",
    )

    key_findings = business_answer.get(
        "key_findings",
        [],
    )

    caveats = business_answer.get(
        "caveats",
        [],
    )

    if not isinstance(key_findings, list):
        key_findings = []

    if not isinstance(caveats, list):
        caveats = []

    # ========================================================
    # 9. CHART INTELLIGENCE
    # ========================================================

    try:
        chart_result = analyze_chart(
            question=data.question,
            rows=rows,
            metrics=selected_metrics,
        )

    except Exception:
        chart_result = {
            "success": True,
            "chart": {
                "type": "table",
                "data": rows,
                "options": {},
            },
            "decision": {
                "chart_type": "table",
                "reason": (
                    "Chart generation was unavailable."
                ),
            },
        }

    chart = chart_result.get(
        "chart",
        {
            "type": "table",
            "data": rows,
            "options": {},
        },
    )

    chart_decision = chart_result.get(
        "decision",
        {},
    )

    # ========================================================
    # 10. MEMORY
    # ========================================================

    summary_json = json.dumps(
        summary,
        default=str,
    )

    chart_type = chart.get(
        "type"
    )

    memory = BusinessMemory(
        workspace_id=workspace.id,
        user_id=current_user.id,
        question=data.question,
        sql_query=executed_sql,
        result_summary=summary_json,
        ai_answer=answer,
        chart_type=chart_type,
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    # ========================================================
    # 11. FINAL BUSINESS AI RESPONSE
    # ========================================================

    return {
        "success": True,
        "answerable": True,

        "question": data.question,

        "answer": answer,

        "key_findings": key_findings,

        "caveats": caveats,

        "sql": executed_sql,

        "reason": sql_result.get(
            "reason",
            "",
        ),

        "summary": summary,

        "rows": rows,

        "metrics": all_metrics,

        "selected_metrics": selected_metrics,

        "chart": chart,

        "chart_decision": chart_decision,

        "memory_id": memory.id,
    }