import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash",
)


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text: str) -> dict:
    if not text:
        raise ValueError("AI returned an empty response.")

    text = text.strip()

    # Remove markdown fences if the model ignored instructions.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # First try the entire response.
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Then find the JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI did not return valid JSON.")

    json_text = text[start:end + 1]

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"AI returned invalid JSON: {str(exc)}"
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("AI JSON response must be an object.")

    return result


# ============================================================
# SCHEMA HELPERS
# ============================================================

def _get_schema_columns(schema: dict) -> list[str]:
    """
    Extract column names from the supported schema structure.

    Supports common formats such as:

    {
        "columns": [
            {"name": "Country", "dtype": "object"}
        ]
    }

    or:

    {
        "columns": ["Country", "Quantity"]
    }
    """

    columns = schema.get("columns", [])

    if not isinstance(columns, list):
        return []

    result = []

    for column in columns:
        if isinstance(column, str):
            result.append(column)

        elif isinstance(column, dict):
            name = (
                column.get("name")
                or column.get("column")
                or column.get("column_name")
            )

            if name:
                result.append(str(name))

    return result


def _find_column(
    schemas: list[dict],
    candidates: list[str],
) -> tuple[str | None, str | None]:
    """
    Find a real column using case-insensitive matching.

    Returns:
        (table_name, column_name)
    """

    candidate_map = {
        candidate.strip().lower()
        for candidate in candidates
    }

    for schema in schemas:
        table_name = schema.get("table_name")

        if not table_name:
            continue

        table_name = str(table_name).strip()

        for column in _get_schema_columns(schema):
            if column.strip().lower() in candidate_map:
                return table_name, column

    return None, None


def _find_country_column(
    schemas: list[dict],
) -> tuple[str | None, str | None]:
    """
    Find the most likely geographic/country column.

    Exact country matching is preferred.
    """

    exact_candidates = [
        "country",
        "country_name",
        "countryname",
    ]

    table_name, column_name = _find_column(
        schemas,
        exact_candidates,
    )

    if table_name and column_name:
        return table_name, column_name

    # Fallback for common variations.
    for schema in schemas:
        table = schema.get("table_name")

        if not table:
            continue

        for column in _get_schema_columns(schema):
            normalized = re.sub(
                r"[^a-z0-9]",
                "",
                column.lower(),
            )

            if normalized in {
                "country",
                "countryname",
            }:
                return str(table), column

    return None, None


def _find_real_table(
    schemas: list[dict],
) -> str | None:
    for schema in schemas:
        table_name = schema.get("table_name")

        if table_name:
            return str(table_name).strip()

    return None


# ============================================================
# DETERMINISTIC RANKING DETECTION
# ============================================================

def _detect_count_question(
    question: str,
    schemas: list[dict],
) -> dict | None:
    normalized = re.sub(
        r"\s+",
        " ",
        question.strip().lower(),
    )

    count_patterns = [
        r"\bhow many\b",
        r"\bnumber of\b",
        r"\bcount of\b",
        r"\btotal number\b",
    ]

    if not any(
        re.search(pattern, normalized)
        for pattern in count_patterns
    ):
        return None

    if not schemas:
        return None

    table_name = str(
        schemas[0].get("table_name") or ""
    ).strip()

    if not table_name:
        return None

    quoted_table = f'"{table_name}"'

    sql = (
        f"SELECT COUNT(*) AS record_count "
        f"FROM {quoted_table}"
    )

    return {
        "answerable": True,
        "sql": sql,
        "reason": (
            "Deterministic row count generated "
            "from the workspace dataset schema."
        ),
    }


def _detect_record_ranking(
    question: str,
    schemas: list[dict],
) -> dict | None:
    """
    Deterministically handles questions asking for countries
    ranked by number of records.

    Examples:

    Which country has the most records?
    Which country has the fewest records?
    Top 10 countries by records
    Bottom 5 countries by number of records
    """

    normalized = re.sub(
        r"\s+",
        " ",
        question.strip().lower(),
    )

    # Must contain a country concept.
    country_words = [
        "country",
        "countries",
    ]

    if not any(word in normalized for word in country_words):
        return None

    # Must contain a record/count concept.
    record_words = [
        "record",
        "records",
        "row",
        "rows",
        "count",
        "counts",
        "number of records",
        "number of rows",
    ]

    if not any(word in normalized for word in record_words):
        return None

    table_name, country_column = _find_country_column(schemas)

    if not table_name or not country_column:
        return None

    # --------------------------------------------------------
    # Direction
    # --------------------------------------------------------

    descending_patterns = [
        r"\bmost\b",
        r"\bhighest\b",
        r"\blargest\b",
        r"\btop\b",
        r"\bmaximum\b",
        r"\bmax\b",
    ]

    ascending_patterns = [
        r"\bleast\b",
        r"\bfewest\b",
        r"\blowest\b",
        r"\bsmallest\b",
        r"\bbottom\b",
        r"\bminimum\b",
        r"\bmin\b",
    ]

    direction = None

    if any(
        re.search(pattern, normalized)
        for pattern in descending_patterns
    ):
        direction = "DESC"

    elif any(
        re.search(pattern, normalized)
        for pattern in ascending_patterns
    ):
        direction = "ASC"

    if direction is None:
        return None

    # --------------------------------------------------------
    # LIMIT
    # --------------------------------------------------------

    limit = None

    # "top 10"
    match = re.search(
        r"\b(?:top|bottom)\s+(\d+)\b",
        normalized,
    )

    if match:
        limit = int(match.group(1))

    # "10 countries with the most records"
    if limit is None:
        match = re.search(
            r"\b(\d+)\s+countries?\b",
            normalized,
        )

        if match:
            limit = int(match.group(1))

    # "which country has..."
    # Means one result.
    if limit is None and re.search(
        r"\bwhich\s+country\b",
        normalized,
    ):
        limit = 1

    # --------------------------------------------------------
    # SQL
    # --------------------------------------------------------

    quoted_table = f'"{table_name}"'
    quoted_country = f'"{country_column}"'

    sql = f"""
SELECT
    {quoted_country},
    COUNT(*) AS record_count
FROM {quoted_table}
WHERE {quoted_country} IS NOT NULL
GROUP BY {quoted_country}
ORDER BY record_count {direction}
""".strip()

    if limit is not None:
        # Keep deterministic ranking bounded.
        limit = max(1, min(limit, 100))
        sql += f"\nLIMIT {limit}"

    return {
        "answerable": True,
        "sql": sql,
        "reason": (
            "Deterministic country record ranking generated "
            "from the workspace schema."
        ),
    }


# ============================================================
# DETERMINISTIC TOTAL REVENUE
# ============================================================

def _detect_revenue_question(
    question: str,
    schemas: list[dict],
) -> dict | None:
    """
    Handles explicit Quantity * UnitPrice revenue questions.

    This avoids unnecessary LLM ambiguity when the metric is
    directly defined by the user.
    """

    normalized = re.sub(
        r"\s+",
        " ",
        question.strip().lower(),
    )

    revenue_terms = [
        "revenue",
        "sales value",
        "sales amount",
    ]

    if not any(
        term in normalized
        for term in revenue_terms
    ):
        return None

    quantity_table, quantity_column = _find_column(
        schemas,
        [
            "quantity",
            "qty",
            "units",
            "unit_quantity",
        ],
    )

    price_table, price_column = _find_column(
        schemas,
        [
            "unitprice",
            "unit_price",
            "price",
            "unit price",
        ],
    )

    if not quantity_table or not quantity_column:
        return None

    if not price_table or not price_column:
        return None

    # Both columns must belong to the same table.
    if quantity_table.lower() != price_table.lower():
        return None

    table_name = quantity_table

    quoted_table = f'"{table_name}"'
    quoted_quantity = f'"{quantity_column}"'
    quoted_price = f'"{price_column}"'

    # Only apply this deterministic rule when the question
    # explicitly defines revenue using multiplication.
    multiplication_terms = [
        "multiplied by",
        "times",
        "quantity *",
        "quantity x",
        "quantity Ã—",
        "quantity multiplied",
        "unitprice",
        "unit price",
    ]

    if not any(
        term in normalized
        for term in multiplication_terms
    ):
        return None

    sql = f"""
SELECT
    SUM(
        COALESCE({quoted_quantity}, 0)
        * COALESCE({quoted_price}, 0)
    ) AS total_revenue
FROM {quoted_table}
""".strip()

    return {
        "answerable": True,
        "sql": sql,
        "reason": (
            "Deterministic revenue calculation generated "
            "from the explicitly defined quantity and price columns."
        ),
    }


# ============================================================
# SQL VALIDATION
# ============================================================

def _validate_generated_sql(
    sql: str,
    schemas: list[dict],
) -> str:

    if not sql:
        raise ValueError("AI returned empty SQL.")

    sql = sql.strip()

    # Remove markdown fences.
    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = re.sub(
        r"\s*```$",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = sql.strip().rstrip(";").strip()

    if not sql:
        raise ValueError("SQL is empty after cleanup.")

    # --------------------------------------------------------
    # READ ONLY
    # --------------------------------------------------------

    lowered = sql.lower()

    if not (
        lowered.startswith("select ")
        or lowered.startswith("with ")
    ):
        raise ValueError(
            "AI generated a non-read-only SQL query."
        )

    # --------------------------------------------------------
    # MULTIPLE STATEMENTS
    # --------------------------------------------------------

    if ";" in sql:
        raise ValueError(
            "AI generated multiple SQL statements."
        )

    # --------------------------------------------------------
    # DANGEROUS SQL
    # --------------------------------------------------------

    forbidden = {
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
        "merge",
        "replace",
    }

    for keyword in forbidden:
        if re.search(
            rf"\b{re.escape(keyword)}\b",
            lowered,
        ):
            raise ValueError(
                f"Unsafe SQL detected: {keyword}"
            )

    # --------------------------------------------------------
    # REAL WORKSPACE TABLES
    # --------------------------------------------------------

    allowed_tables = {
        str(item.get("table_name", "")).strip().lower()
        for item in schemas
        if item.get("table_name")
    }

    if not allowed_tables:
        raise ValueError(
            "No valid workspace tables were supplied."
        )

    # --------------------------------------------------------
    # PLACEHOLDER TABLE NAMES
    # --------------------------------------------------------

    placeholders = {
        "table_name",
        "your_table",
        "my_table",
        "dataset",
        "your_dataset",
        "my_dataset",
        "table",
        "tablename",
    }

    for placeholder in placeholders:
        if re.search(
            rf'(?:"{re.escape(placeholder)}"|'
            rf'`{re.escape(placeholder)}`|'
            rf'\b{re.escape(placeholder)}\b)',
            sql,
            flags=re.IGNORECASE,
        ):
            raise ValueError(
                f"AI generated placeholder table name: {placeholder}"
            )

    # --------------------------------------------------------
    # FIND TABLES AFTER FROM / JOIN
    # --------------------------------------------------------

    table_pattern = re.compile(
        r"""
        \b(?:from|join)\s+
        (?:
            "(?P<double>[a-zA-Z0-9_]+)"
            |
            `(?P<backtick>[a-zA-Z0-9_]+)`
            |
            (?P<plain>[a-zA-Z0-9_]+)
        )
        """,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    matches = table_pattern.finditer(sql)

    referenced_tables = []

    for match in matches:
        table_name = (
            match.group("double")
            or match.group("backtick")
            or match.group("plain")
        )

        if table_name:
            referenced_tables.append(
                table_name.lower()
            )

    if not referenced_tables:
        raise ValueError(
            "SQL does not reference a workspace dataset."
        )

    for table_name in referenced_tables:
        if table_name not in allowed_tables:
            raise ValueError(
                f"Table '{table_name}' is not available in this workspace."
            )

    return sql


# ============================================================
# MAIN SQL GENERATOR
# ============================================================

def generate_sql(
    question: str,
    schemas: list[dict],
) -> dict:

    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    if not schemas:
        raise ValueError(
            "No dataset schemas were provided."
        )

    question = question.strip()

    # ========================================================
    # IMPORTANT:
    # Deterministic business intents run BEFORE Gemini.
    # ========================================================

    count_result = _detect_count_question(
        question=question,
        schemas=schemas,
    )

    if count_result:
        count_result["sql"] = _validate_generated_sql(
            sql=count_result["sql"],
            schemas=schemas,
        )

        return count_result

    ranking_result = _detect_record_ranking(
        question=question,
        schemas=schemas,
    )

    if ranking_result:
        ranking_result["sql"] = _validate_generated_sql(
            sql=ranking_result["sql"],
            schemas=schemas,
        )

        return ranking_result

    revenue_result = _detect_revenue_question(
        question=question,
        schemas=schemas,
    )

    if revenue_result:
        revenue_result["sql"] = _validate_generated_sql(
            sql=revenue_result["sql"],
            schemas=schemas,
        )

        return revenue_result

    # ========================================================
    # LLM FALLBACK
    # ========================================================

    schema_text = json.dumps(
        schemas,
        indent=2,
        default=str,
    )

    real_tables = [
        str(item.get("table_name"))
        for item in schemas
        if item.get("table_name")
    ]

    real_table_text = "\n".join(
        f"- {table}"
        for table in real_tables
    )

    system_prompt = f"""
You are Aloko Business AI's SQL Intelligence Engine.

Your job is to translate a natural-language business question
into SAFE PostgreSQL SQL.

============================================================
REAL WORKSPACE TABLES
============================================================

These are the ONLY real tables you may use:

{real_table_text}

IMPORTANT:

You MUST use one of the exact table names listed above.

NEVER use:

"table_name"
"your_table"
"my_table"
"dataset"
"your_dataset"
"my_dataset"
"table"
"tablename"

============================================================
CORE RULES
============================================================

1. Only use tables provided in the workspace schemas.
2. Only use columns explicitly provided in the schemas.
3. Never invent a table.
4. Never invent a column.
5. Only generate SELECT or WITH queries.
6. Never generate INSERT.
7. Never generate UPDATE.
8. Never generate DELETE.
9. Never generate DROP.
10. Never generate ALTER.
11. Never generate CREATE.
12. Never generate TRUNCATE.
13. Never modify the database.
14. Use PostgreSQL syntax.
15. ALWAYS double-quote table names.
16. ALWAYS double-quote column names.
17. Preserve column capitalization exactly.
18. Preserve table capitalization exactly.

============================================================
NUMERIC DATA TYPES
============================================================

Different numeric types CAN be used together.

For example:

Quantity = int64
UnitPrice = float64

This is valid PostgreSQL arithmetic:

"Quantity" * "UnitPrice"

Do NOT mark a question unanswerable because numeric
columns have different numeric types.

============================================================
CALCULATED METRICS
============================================================

When the user defines a metric using arithmetic, calculate it
directly from the available columns.

============================================================
BUSINESS AGGREGATIONS
============================================================

"total" -> SUM()
"how many" -> COUNT()
"count" -> COUNT()
"average" -> AVG()
"mean" -> AVG()
"minimum" -> MIN()
"maximum" -> MAX()

============================================================
RANKING
============================================================

For ranking questions:

"most", "highest", "largest", "top"
-> descending order

"least", "fewest", "lowest", "smallest", "bottom"
-> ascending order

For example:

SELECT
    "Country",
    COUNT(*) AS record_count
FROM "REAL_TABLE"
GROUP BY "Country"
ORDER BY record_count DESC
LIMIT 1;

============================================================
NULL HANDLING
============================================================

Use COALESCE when appropriate for arithmetic involving
nullable numeric columns.

============================================================
DATE ANALYSIS
============================================================

Monthly:

DATE_TRUNC('month', "ActualDateColumn")

Yearly:

DATE_TRUNC('year', "ActualDateColumn")

Daily:

DATE_TRUNC('day', "ActualDateColumn")

Only use actual date columns from the schema.

============================================================
ANSWERABILITY
============================================================

Return answerable=true when the question can reasonably be
answered using the provided columns.

Do NOT mark a question unanswerable merely because:

- arithmetic is required
- multiplication is required
- division is required
- aggregation is required
- grouping is required
- sorting is required
- ranking is required
- numeric types differ
- a calculated metric is required

Return answerable=false ONLY when the required information
genuinely does not exist in the schemas.

============================================================
WORKSPACE SCHEMAS
============================================================

{schema_text}

============================================================
FINAL RESPONSE FORMAT
============================================================

Return JSON ONLY.

For answerable questions:

{{
  "answerable": true,
  "sql": "SELECT ...",
  "reason": "Short explanation"
}}

For unanswerable questions:

{{
  "answerable": false,
  "sql": null,
  "reason": "Why the question genuinely cannot be answered"
}}

Never return Markdown.
Never return code fences.
Never return text outside the JSON object.
"""

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured for Business AI."
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            system_prompt
                            + "\n\nUSER BUSINESS QUESTION:\n"
                            + question
                        )
                    }
                ],
            }
        ],
    }

    response = requests.post(
        GEMINI_API_URL.format(model=GEMINI_MODEL),
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data
        .get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    result = _extract_json(content)

    if "answerable" not in result:
        raise ValueError(
            "AI response is missing 'answerable'."
        )

    if result.get("answerable"):
        generated_sql = result.get("sql")

        if not generated_sql:
            raise ValueError(
                "AI marked the question answerable "
                "but returned no SQL."
            )

        validated_sql = _validate_generated_sql(
            sql=generated_sql,
            schemas=schemas,
        )

        result["sql"] = validated_sql

    else:
        result["sql"] = None

    return result
