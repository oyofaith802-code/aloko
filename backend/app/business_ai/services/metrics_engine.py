import re
from typing import Any


# ============================================================
# ALoko BUSINESS METRICS ENGINE
# ============================================================
#
# Schema-driven metric detection.
#
# This engine does NOT assume a specific industry.
#
# It examines:
#   - column names
#   - data types
#   - question
#   - dataset profile
#
# and identifies useful business metrics that can reasonably
# be calculated from the available data.
# ============================================================


# ------------------------------------------------------------
# Column name patterns
# ------------------------------------------------------------

REVENUE_PATTERNS = [
    r"\brevenue\b",
    r"\bsales\b",
    r"\bsale_amount\b",
    r"\bsales_amount\b",
    r"\bturnover\b",
    r"\bincome\b",
    r"\btotal_amount\b",
    r"\border_value\b",
    r"\bamount\b",
]

COST_PATTERNS = [
    r"\bcost\b",
    r"\bcosts\b",
    r"\bexpense\b",
    r"\bexpenses\b",
    r"\bpurchase_cost\b",
    r"\bunit_cost\b",
]

PROFIT_PATTERNS = [
    r"\bprofit\b",
    r"\bnet_profit\b",
    r"\bgross_profit\b",
    r"\bprofit_amount\b",
]

QUANTITY_PATTERNS = [
    r"\bquantity\b",
    r"\bqty\b",
    r"\bunits\b",
    r"\bunit_count\b",
    r"\bvolume\b",
]

CUSTOMER_PATTERNS = [
    r"\bcustomer\b",
    r"\bcustomer_id\b",
    r"\bclient\b",
    r"\bclient_id\b",
    r"\bbuyer\b",
    r"\buser_id\b",
]

ORDER_PATTERNS = [
    r"\border\b",
    r"\border_id\b",
    r"\binvoice\b",
    r"\binvoice_no\b",
    r"\btransaction\b",
    r"\btransaction_id\b",
    r"\breceipt\b",
]

PRODUCT_PATTERNS = [
    r"\bproduct\b",
    r"\bproduct_id\b",
    r"\bitem\b",
    r"\bitem_id\b",
    r"\bsku\b",
    r"\bstockcode\b",
    r"\bstock_code\b",
]

DATE_PATTERNS = [
    r"\bdate\b",
    r"\bdatetime\b",
    r"\btime\b",
    r"\bcreated_at\b",
    r"\bupdated_at\b",
    r"\border_date\b",
    r"\bsale_date\b",
    r"\btransaction_date\b",
    r"\binvoice_date\b",
    r"\bpurchase_date\b",
]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _normalize_name(value: str) -> str:
    value = str(value or "").strip().lower()
    value = value.replace("-", "_")
    value = re.sub(r"\s+", "_", value)
    return value


def _matches_any(
    column_name: str,
    patterns: list[str],
) -> bool:

    normalized = _normalize_name(column_name)

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


def _column_type(column: dict) -> str:
    return str(
        column.get("dtype", "")
    ).lower()


def _is_numeric(column: dict) -> bool:
    dtype = _column_type(column)

    numeric_types = {
        "int",
        "int8",
        "int16",
        "int32",
        "int64",
        "float",
        "float16",
        "float32",
        "float64",
        "double",
        "decimal",
        "numeric",
    }

    return any(
        numeric_type in dtype
        for numeric_type in numeric_types
    )


def _is_datetime(column: dict) -> bool:
    dtype = _column_type(column)

    return (
        "datetime" in dtype
        or "timestamp" in dtype
        or dtype.startswith("date")
    )


# ------------------------------------------------------------
# Detect columns
# ------------------------------------------------------------

def detect_business_columns(
    schema: dict,
) -> dict[str, list[dict[str, Any]]]:

    columns = schema.get("columns", [])

    detected = {
        "revenue": [],
        "cost": [],
        "profit": [],
        "quantity": [],
        "customer": [],
        "order": [],
        "product": [],
        "date": [],
        "numeric": [],
        "categorical": [],
    }

    for column in columns:

        name = str(
            column.get("name", "")
        )

        if not name:
            continue

        if _matches_any(
            name,
            REVENUE_PATTERNS,
        ):
            detected["revenue"].append(column)

        if _matches_any(
            name,
            COST_PATTERNS,
        ):
            detected["cost"].append(column)

        if _matches_any(
            name,
            PROFIT_PATTERNS,
        ):
            detected["profit"].append(column)

        if _matches_any(
            name,
            QUANTITY_PATTERNS,
        ):
            detected["quantity"].append(column)

        if _matches_any(
            name,
            CUSTOMER_PATTERNS,
        ):
            detected["customer"].append(column)

        if _matches_any(
            name,
            ORDER_PATTERNS,
        ):
            detected["order"].append(column)

        if _matches_any(
            name,
            PRODUCT_PATTERNS,
        ):
            detected["product"].append(column)

        if (
            _matches_any(
                name,
                DATE_PATTERNS,
            )
            or _is_datetime(column)
        ):
            detected["date"].append(column)

        if _is_numeric(column):
            detected["numeric"].append(column)

        dtype = _column_type(column)

        if (
            "object" in dtype
            or "category" in dtype
            or "bool" in dtype
            or "string" in dtype
        ):
            detected["categorical"].append(column)

    return detected


# ------------------------------------------------------------
# Choose best candidate
# ------------------------------------------------------------

def _first_column(
    columns: list[dict],
) -> str | None:

    if not columns:
        return None

    name = columns[0].get("name")

    if not name:
        return None

    return str(name)


# ------------------------------------------------------------
# Metric creation
# ------------------------------------------------------------

def _metric(
    name: str,
    metric_type: str,
    description: str,
    expression: str | None = None,
    columns: list[str] | None = None,
    confidence: float = 1.0,
) -> dict[str, Any]:

    return {
        "name": name,
        "type": metric_type,
        "description": description,
        "expression": expression,
        "columns": columns or [],
        "confidence": confidence,
    }


# ------------------------------------------------------------
# Automatic metric detection
# ------------------------------------------------------------

def detect_metrics(
    schema: dict,
    profile: dict | None = None,
) -> list[dict[str, Any]]:

    detected = detect_business_columns(
        schema
    )

    metrics = []

    revenue_column = _first_column(
        detected["revenue"]
    )

    cost_column = _first_column(
        detected["cost"]
    )

    profit_column = _first_column(
        detected["profit"]
    )

    quantity_column = _first_column(
        detected["quantity"]
    )

    customer_column = _first_column(
        detected["customer"]
    )

    order_column = _first_column(
        detected["order"]
    )

    product_column = _first_column(
        detected["product"]
    )

    date_column = _first_column(
        detected["date"]
    )

    # ========================================================
    # DIRECT REVENUE
    # ========================================================

    if revenue_column:

        metrics.append(
            _metric(
                name="Revenue",
                metric_type="currency",
                description=(
                    f"Total revenue based on {revenue_column}."
                ),
                expression=(
                    f'SUM("{revenue_column}")'
                ),
                columns=[revenue_column],
                confidence=0.95,
            )
        )

    # ========================================================
    # DIRECT COST
    # ========================================================

    if cost_column:

        metrics.append(
            _metric(
                name="Cost",
                metric_type="currency",
                description=(
                    f"Total cost based on {cost_column}."
                ),
                expression=(
                    f'SUM("{cost_column}")'
                ),
                columns=[cost_column],
                confidence=0.95,
            )
        )

    # ========================================================
    # DIRECT PROFIT
    # ========================================================

    if profit_column:

        metrics.append(
            _metric(
                name="Profit",
                metric_type="currency",
                description=(
                    f"Total profit based on {profit_column}."
                ),
                expression=(
                    f'SUM("{profit_column}")'
                ),
                columns=[profit_column],
                confidence=0.97,
            )
        )

    # ========================================================
    # DERIVED PROFIT
    # ========================================================

    if revenue_column and cost_column:

        metrics.append(
            _metric(
                name="Profit",
                metric_type="currency",
                description=(
                    "Revenue minus cost."
                ),
                expression=(
                    f'SUM("{revenue_column}") '
                    f'- SUM("{cost_column}")'
                ),
                columns=[
                    revenue_column,
                    cost_column,
                ],
                confidence=0.90,
            )
        )

        metrics.append(
            _metric(
                name="Profit Margin",
                metric_type="percentage",
                description=(
                    "Profit as a percentage of revenue."
                ),
                expression=(
                    f"""
                    CASE
                        WHEN SUM("{revenue_column}") = 0
                        THEN 0
                        ELSE
                            (
                                (
                                    SUM("{revenue_column}")
                                    - SUM("{cost_column}")
                                )
                                / SUM("{revenue_column}")
                            ) * 100
                    END
                    """.strip()
                ),
                columns=[
                    revenue_column,
                    cost_column,
                ],
                confidence=0.88,
            )
        )

    # ========================================================
    # QUANTITY
    # ========================================================

    if quantity_column:

        metrics.append(
            _metric(
                name="Units Sold",
                metric_type="quantity",
                description=(
                    f"Total quantity based on {quantity_column}."
                ),
                expression=(
                    f'SUM("{quantity_column}")'
                ),
                columns=[quantity_column],
                confidence=0.93,
            )
        )

    # ========================================================
    # CUSTOMER COUNT
    # ========================================================

    if customer_column:

        metrics.append(
            _metric(
                name="Customers",
                metric_type="count",
                description=(
                    f"Distinct customers based on {customer_column}."
                ),
                expression=(
                    f'COUNT(DISTINCT "{customer_column}")'
                ),
                columns=[customer_column],
                confidence=0.94,
            )
        )

    # ========================================================
    # ORDER COUNT
    # ========================================================

    if order_column:

        metrics.append(
            _metric(
                name="Orders",
                metric_type="count",
                description=(
                    f"Distinct orders based on {order_column}."
                ),
                expression=(
                    f'COUNT(DISTINCT "{order_column}")'
                ),
                columns=[order_column],
                confidence=0.91,
            )
        )

    else:

        # Every dataset has records even if it does not have
        # an obvious order identifier.

        metrics.append(
            _metric(
                name="Records",
                metric_type="count",
                description=(
                    "Total number of records in the dataset."
                ),
                expression="COUNT(*)",
                columns=[],
                confidence=1.0,
            )
        )

    # ========================================================
    # PRODUCT COUNT
    # ========================================================

    if product_column:

        metrics.append(
            _metric(
                name="Products",
                metric_type="count",
                description=(
                    f"Distinct products based on {product_column}."
                ),
                expression=(
                    f'COUNT(DISTINCT "{product_column}")'
                ),
                columns=[product_column],
                confidence=0.92,
            )
        )

    # ========================================================
    # AVERAGE ORDER VALUE
    # ========================================================

    if revenue_column and order_column:

        metrics.append(
            _metric(
                name="Average Order Value",
                metric_type="currency",
                description=(
                    "Average revenue per distinct order."
                ),
                expression=(
                    f"""
                    CASE
                        WHEN COUNT(DISTINCT "{order_column}") = 0
                        THEN 0
                        ELSE
                            SUM("{revenue_column}")
                            /
                            COUNT(DISTINCT "{order_column}")
                    END
                    """.strip()
                ),
                columns=[
                    revenue_column,
                    order_column,
                ],
                confidence=0.90,
            )
        )

    # ========================================================
    # AVERAGE ORDER VALUE FROM QUANTITY × UNIT PRICE
    # ========================================================

    if (
        not revenue_column
        and quantity_column
        and order_column
    ):

        numeric_candidates = [
            column
            for column in detected["numeric"]
            if column.get("name") != quantity_column
        ]

        unit_price = None

        for column in numeric_candidates:

            name = _normalize_name(
                column.get("name", "")
            )

            if (
                "price" in name
                or "unit_price" in name
                or "selling_price" in name
            ):
                unit_price = str(
                    column.get("name")
                )
                break

        if unit_price:

            expression = (
                f'SUM("{quantity_column}" * "{unit_price}")'
            )

            metrics.append(
                _metric(
                    name="Revenue",
                    metric_type="currency",
                    description=(
                        "Revenue calculated from quantity "
                        "multiplied by unit price."
                    ),
                    expression=expression,
                    columns=[
                        quantity_column,
                        unit_price,
                    ],
                    confidence=0.88,
                )
            )

            metrics.append(
                _metric(
                    name="Average Order Value",
                    metric_type="currency",
                    description=(
                        "Average calculated revenue per order."
                    ),
                    expression=(
                        f"""
                        CASE
                            WHEN COUNT(DISTINCT "{order_column}") = 0
                            THEN 0
                            ELSE
                                SUM(
                                    "{quantity_column}"
                                    * "{unit_price}"
                                )
                                /
                                COUNT(DISTINCT "{order_column}")
                        END
                        """.strip()
                    ),
                    columns=[
                        quantity_column,
                        unit_price,
                        order_column,
                    ],
                    confidence=0.82,
                )
            )

    # ========================================================
    # DATE / TREND CAPABILITY
    # ========================================================

    if date_column:

        metrics.append(
            _metric(
                name="Time Trend",
                metric_type="trend",
                description=(
                    f"Time-based analysis using {date_column}."
                ),
                expression=None,
                columns=[date_column],
                confidence=0.90,
            )
        )

        metrics.append(
            _metric(
                name="Monthly Trend",
                metric_type="trend",
                description=(
                    f"Monthly aggregation using {date_column}."
                ),
                expression=(
                    f'DATE_TRUNC(\'month\', "{date_column}")'
                ),
                columns=[date_column],
                confidence=0.90,
            )
        )

    # ========================================================
    # REMOVE DUPLICATE METRIC NAMES
    # ========================================================

    unique = {}

    for metric in metrics:

        name = metric["name"]

        existing = unique.get(name)

        if (
            existing is None
            or metric["confidence"]
            > existing["confidence"]
        ):
            unique[name] = metric

    return list(unique.values())


# ------------------------------------------------------------
# Question-aware metric selection
# ------------------------------------------------------------

def select_metrics_for_question(
    question: str,
    metrics: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    question_lower = (
        question or ""
    ).lower()

    selected = []

    keyword_map = {
        "revenue": ["revenue", "sales", "turnover", "income"],
        "profit": ["profit", "margin"],
        "cost": ["cost", "costs", "expense", "expenses"],
        "customer": ["customer", "customers", "client", "clients"],
        "order": ["order", "orders", "transaction", "transactions"],
        "product": ["product", "products", "item", "items"],
        "quantity": ["quantity", "units", "volume"],
        "trend": [
            "trend",
            "growth",
            "decline",
            "increase",
            "decrease",
            "monthly",
            "yearly",
            "daily",
            "over time",
        ],
    }

    for metric in metrics:

        name = metric["name"].lower()

        matched = False

        for metric_group, keywords in keyword_map.items():

            if metric_group not in name:
                continue

            if any(
                keyword in question_lower
                for keyword in keywords
            ):
                matched = True
                break

        if matched:
            selected.append(metric)

    # If nothing specifically matched, return the strongest
    # generally useful metrics.

    if not selected:

        selected = sorted(
            metrics,
            key=lambda item: item.get(
                "confidence",
                0,
            ),
            reverse=True,
        )[:8]

    return selected


# ------------------------------------------------------------
# Full engine
# ------------------------------------------------------------

def analyze_business_metrics(
    schema: dict,
    profile: dict | None = None,
    question: str | None = None,
) -> dict[str, Any]:

    metrics = detect_metrics(
        schema=schema,
        profile=profile,
    )

    selected_metrics = metrics

    if question:

        selected_metrics = select_metrics_for_question(
            question=question,
            metrics=metrics,
        )

    return {
        "success": True,
        "metrics": metrics,
        "selected_metrics": selected_metrics,
        "detected_columns": detect_business_columns(
            schema
        ),
    }