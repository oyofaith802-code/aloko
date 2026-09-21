from typing import Any


# ============================================================
# CHART INTELLIGENCE
# ============================================================

def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_numeric(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, bool):
        return False

    return isinstance(value, (int, float))


def _looks_like_date_column(name: str) -> bool:
    name = _lower(name)

    date_words = [
        "date",
        "time",
        "month",
        "year",
        "day",
        "created",
        "updated",
        "timestamp",
    ]

    return any(word in name for word in date_words)


def _looks_categorical_column(name: str) -> bool:
    name = _lower(name)

    categorical_words = [
        "country",
        "category",
        "type",
        "status",
        "region",
        "state",
        "city",
        "product",
        "item",
        "customer",
        "department",
        "segment",
        "channel",
        "brand",
        "gender",
    ]

    return any(word in name for word in categorical_words)


def _detect_column_types(
    rows: list[dict[str, Any]],
) -> dict[str, list[str]]:
    if not rows:
        return {
            "numeric": [],
            "date": [],
            "categorical": [],
        }

    columns = list(rows[0].keys())

    numeric = []
    date_columns = []
    categorical = []

    for column in columns:
        values = [
            row.get(column)
            for row in rows
            if row.get(column) is not None
        ]

        if not values:
            continue

        numeric_ratio = sum(
            _is_numeric(value)
            for value in values[:100]
        ) / min(len(values), 100)

        if numeric_ratio >= 0.8:
            numeric.append(column)
            continue

        if _looks_like_date_column(column):
            date_columns.append(column)
            continue

        if _looks_categorical_column(column):
            categorical.append(column)
            continue

        categorical.append(column)

    return {
        "numeric": numeric,
        "date": date_columns,
        "categorical": categorical,
    }


def choose_chart_type(
    question: str,
    rows: list[dict[str, Any]],
    metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    question_lower = _lower(question)

    if not rows:
        return {
            "chart_type": "none",
            "reason": "No result rows are available for visualization.",
        }

    column_types = _detect_column_types(rows)

    numeric_columns = column_types["numeric"]
    date_columns = column_types["date"]
    categorical_columns = column_types["categorical"]

    # --------------------------------------------------------
    # TIME SERIES
    # --------------------------------------------------------

    trend_words = [
        "trend",
        "growth",
        "decline",
        "over time",
        "monthly",
        "weekly",
        "daily",
        "yearly",
        "year over year",
        "month over month",
    ]

    if (
        date_columns
        and any(word in question_lower for word in trend_words)
    ):
        return {
            "chart_type": "line",
            "x_column": date_columns[0],
            "y_column": numeric_columns[0] if numeric_columns else None,
            "reason": "A time-based question is best represented with a line chart.",
        }

    # --------------------------------------------------------
    # PIE / DONUT
    # --------------------------------------------------------

    proportion_words = [
        "share",
        "percentage",
        "percent",
        "proportion",
        "distribution",
        "breakdown",
        "split",
    ]

    if (
        categorical_columns
        and numeric_columns
        and any(word in question_lower for word in proportion_words)
        and len(rows) <= 15
    ):
        return {
            "chart_type": "donut",
            "label_column": categorical_columns[0],
            "value_column": numeric_columns[0],
            "reason": "The question asks for a proportional breakdown.",
        }

    # --------------------------------------------------------
    # RANKING
    # --------------------------------------------------------

    ranking_words = [
        "top",
        "bottom",
        "highest",
        "lowest",
        "most",
        "least",
        "best",
        "worst",
        "rank",
        "ranking",
    ]

    if (
        categorical_columns
        and numeric_columns
        and any(word in question_lower for word in ranking_words)
    ):
        return {
            "chart_type": "bar",
            "x_column": categorical_columns[0],
            "y_column": numeric_columns[0],
            "orientation": "horizontal",
            "reason": "Ranking and category comparison are best represented with a bar chart.",
        }

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    comparison_words = [
        "compare",
        "comparison",
        "by country",
        "by category",
        "by product",
        "by region",
        "by customer",
        "by department",
        "by channel",
    ]

    if (
        categorical_columns
        and numeric_columns
        and any(word in question_lower for word in comparison_words)
    ):
        return {
            "chart_type": "bar",
            "x_column": categorical_columns[0],
            "y_column": numeric_columns[0],
            "orientation": "vertical",
            "reason": "Category comparison is best represented with a bar chart.",
        }

    # --------------------------------------------------------
    # MANY CATEGORIES
    # --------------------------------------------------------

    if (
        categorical_columns
        and numeric_columns
        and len(rows) <= 50
    ):
        return {
            "chart_type": "bar",
            "x_column": categorical_columns[0],
            "y_column": numeric_columns[0],
            "orientation": "vertical",
            "reason": "The result contains categorical and numeric values suitable for comparison.",
        }

    # --------------------------------------------------------
    # TWO NUMERIC VARIABLES
    # --------------------------------------------------------

    if len(numeric_columns) >= 2:
        return {
            "chart_type": "scatter",
            "x_column": numeric_columns[0],
            "y_column": numeric_columns[1],
            "reason": "Two numeric variables can be compared using a scatter plot.",
        }

    # --------------------------------------------------------
    # SINGLE NUMERIC RESULT
    # --------------------------------------------------------

    if len(numeric_columns) == 1:
        return {
            "chart_type": "kpi",
            "value_column": numeric_columns[0],
            "reason": "A single numeric result is best presented as a KPI.",
        }

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return {
        "chart_type": "table",
        "reason": "The result is better represented as a data table.",
    }


def build_chart_config(
    question: str,
    rows: list[dict[str, Any]],
    metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    decision = choose_chart_type(
        question=question,
        rows=rows,
        metrics=metrics,
    )

    chart_type = decision.get("chart_type")

    config = {
        "type": chart_type,
        "data": rows,
        "options": {},
    }

    if chart_type == "bar":
        config["options"] = {
            "x_column": decision.get("x_column"),
            "y_column": decision.get("y_column"),
            "orientation": decision.get(
                "orientation",
                "vertical",
            ),
        }

    elif chart_type == "line":
        config["options"] = {
            "x_column": decision.get("x_column"),
            "y_column": decision.get("y_column"),
        }

    elif chart_type == "donut":
        config["options"] = {
            "label_column": decision.get("label_column"),
            "value_column": decision.get("value_column"),
        }

    elif chart_type == "scatter":
        config["options"] = {
            "x_column": decision.get("x_column"),
            "y_column": decision.get("y_column"),
        }

    elif chart_type == "kpi":
        config["options"] = {
            "value_column": decision.get("value_column"),
        }

    return {
        "success": True,
        "chart": config,
        "decision": decision,
    }


def analyze_chart(
    question: str,
    rows: list[dict[str, Any]],
    metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    return build_chart_config(
        question=question,
        rows=rows,
        metrics=metrics,
    )