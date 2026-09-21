from datetime import datetime, timezone
from typing import Any


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def build_business_report(
    title: str,
    question: str,
    datasets: list[dict[str, Any]],
    summary: dict[str, Any],
    answer: str,
    key_findings: list[str],
    caveats: list[str],
    metrics: list[dict[str, Any]],
    selected_metrics: list[dict[str, Any]],
    chart: dict[str, Any],
    chart_decision: dict[str, Any],
) -> dict[str, Any]:

    summary = _safe_dict(summary)
    chart = _safe_dict(chart)
    chart_decision = _safe_dict(chart_decision)

    key_findings = _safe_list(key_findings)
    caveats = _safe_list(caveats)
    metrics = _safe_list(metrics)
    selected_metrics = _safe_list(selected_metrics)
    datasets = _safe_list(datasets)

    report_datasets = []

    for dataset in datasets:
        if not isinstance(dataset, dict):
            continue

        report_datasets.append(
            {
                "dataset_id": dataset.get("dataset_id"),
                "name": dataset.get("dataset_name"),
                "source_type": dataset.get("source_type"),
                "row_count": dataset.get("row_count"),
            }
        )

    report = {
        "report_version": "1.0",

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "title": title,

        "report_type": "business_analysis",

        "question": question,

        "executive_summary": {
            "answer": answer,
            "key_findings": key_findings,
            "caveats": caveats,
        },

        "datasets": report_datasets,

        "kpis": selected_metrics,

        "available_metrics": metrics,

        "results": {
            "row_count": summary.get("row_count", 0),
            "columns": summary.get("columns", []),
            "rows": summary.get("rows", []),
        },

        "visualization": {
            "type": chart.get("type", "table"),
            "data": chart.get("data", []),
            "options": chart.get("options", {}),
            "decision": chart_decision,
        },

        "sections": [
            {
                "id": "executive_summary",
                "title": "Executive Summary",
                "content": answer,
            },
            {
                "id": "key_findings",
                "title": "Key Findings",
                "items": key_findings,
            },
            {
                "id": "kpis",
                "title": "Key Performance Indicators",
                "items": selected_metrics,
            },
            {
                "id": "visualization",
                "title": "Visualization",
                "chart_type": chart.get(
                    "type",
                    "table",
                ),
            },
            {
                "id": "caveats",
                "title": "Caveats",
                "items": caveats,
            },
        ],
    }

    return report