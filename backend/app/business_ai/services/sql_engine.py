import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine


# ============================================================
# SQL SAFETY CONFIGURATION
# ============================================================

FORBIDDEN_SQL_KEYWORDS = {
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
    "comment",
    "vacuum",
    "analyze",
    "refresh",
    "cluster",
    "reindex",
}

FORBIDDEN_FUNCTIONS = {
    "pg_sleep",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "pg_stat_file",
    "lo_import",
    "lo_export",
    "dblink_connect",
    "dblink_exec",
}

FORBIDDEN_SYSTEM_PATTERNS = [
    r"\bpg_catalog\b",
    r"\binformation_schema\b",
    r"\bpg_toast\b",
    r"\bpg_temp\b",
    r"\bpg_internal\b",
]

DEFAULT_MAX_ROWS = 500
ABSOLUTE_MAX_ROWS = 5000

DEFAULT_QUERY_TIMEOUT_MS = 30000
MAX_QUERY_TIMEOUT_MS = 60000

MAX_SQL_LENGTH = 20000


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_sql(sql: str) -> str:
    """
    Normalize AI-generated SQL.

    Removes Markdown SQL fences and trailing semicolons.
    """

    if not sql:
        raise ValueError("SQL query is empty.")

    sql = sql.strip()

    # Remove opening markdown fence:
    # ```sql
    # ```
    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    # Remove closing markdown fence.
    sql = re.sub(
        r"\s*```$",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = sql.strip()

    if len(sql) > MAX_SQL_LENGTH:
        raise ValueError("SQL query is too large.")

    # Only remove trailing semicolons.
    # Internal semicolons are still rejected later.
    sql = sql.rstrip(";").strip()

    if not sql:
        raise ValueError("SQL query is empty.")

    return sql


# ============================================================
# COMMENT PROTECTION
# ============================================================

def remove_sql_comments(sql: str) -> str:
    """
    Remove SQL comments before safety inspection.

    This prevents dangerous SQL from being hidden inside
    comments or confusing the validator.
    """

    # Block comments: /* ... */
    sql = re.sub(
        r"/\*.*?\*/",
        " ",
        sql,
        flags=re.DOTALL,
    )

    # Single-line comments: -- ...
    sql = re.sub(
        r"--[^\r\n]*",
        " ",
        sql,
    )

    return sql


# ============================================================
# STATEMENT VALIDATION
# ============================================================

def validate_single_statement(sql: str) -> None:
    """
    Ensure only one SQL statement is submitted.
    """

    if ";" in sql:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )


def validate_read_only_statement(sql: str) -> None:
    """
    Only SELECT and WITH queries are permitted.
    """

    lowered = sql.lower().strip()

    if not (
        lowered.startswith("select ")
        or lowered.startswith("select\n")
        or lowered == "select"
        or lowered.startswith("with ")
        or lowered.startswith("with\n")
    ):
        raise ValueError(
            "Only read-only SELECT queries are allowed."
        )


# ============================================================
# DANGEROUS KEYWORD DETECTION
# ============================================================

def validate_forbidden_keywords(sql: str) -> None:
    inspection_sql = remove_sql_comments(sql).lower()

    for keyword in FORBIDDEN_SQL_KEYWORDS:
        pattern = rf"\b{re.escape(keyword)}\b"

        if re.search(
            pattern,
            inspection_sql,
        ):
            raise ValueError(
                f"Unsafe SQL detected: {keyword}"
            )


# ============================================================
# DANGEROUS FUNCTION DETECTION
# ============================================================

def validate_forbidden_functions(sql: str) -> None:
    inspection_sql = remove_sql_comments(sql).lower()

    for function_name in FORBIDDEN_FUNCTIONS:
        pattern = rf"\b{re.escape(function_name)}\s*\("

        if re.search(
            pattern,
            inspection_sql,
        ):
            raise ValueError(
                "Unsafe SQL function detected."
            )


# ============================================================
# SYSTEM TABLE PROTECTION
# ============================================================

def validate_system_objects(sql: str) -> None:
    inspection_sql = remove_sql_comments(sql).lower()

    for pattern in FORBIDDEN_SYSTEM_PATTERNS:
        if re.search(
            pattern,
            inspection_sql,
        ):
            raise ValueError(
                "Access to system database objects is not allowed."
            )


# ============================================================
# TABLE EXTRACTION
# ============================================================

def extract_referenced_tables(sql: str) -> list[str]:
    """
    Extract tables referenced by FROM and JOIN.

    Supports:

        FROM table_name
        FROM "table_name"
        JOIN table_name
        JOIN "table_name"

    Also supports optional PostgreSQL schema qualification.
    """

    inspection_sql = remove_sql_comments(sql)

    table_pattern = re.compile(
        r"""
        \b
        (?:from|join)
        \s+
        (?:
            (?:
                ["`]
                ([a-zA-Z0-9_]+)
                ["`]
            )
            |
            ([a-zA-Z0-9_]+)
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    matches = table_pattern.findall(
        inspection_sql
    )

    tables: list[str] = []

    for quoted_name, plain_name in matches:
        table_name = quoted_name or plain_name

        if table_name:
            tables.append(table_name)

    return tables


# ============================================================
# WORKSPACE TABLE VALIDATION
# ============================================================

def validate_workspace_tables(
    sql: str,
    allowed_tables: list[str],
) -> None:
    """
    Ensure every referenced table belongs to the
    current Business AI workspace.
    """

    if not allowed_tables:
        raise ValueError(
            "No datasets are available in this workspace."
        )

    referenced_tables = extract_referenced_tables(sql)

    if not referenced_tables:
        raise ValueError(
            "SQL must reference a workspace dataset."
        )

    allowed_set = {
        table.lower()
        for table in allowed_tables
    }

    for table in referenced_tables:
        if table.lower() not in allowed_set:
            raise ValueError(
                f"Table '{table}' is not available "
                "in this workspace."
            )


# ============================================================
# LIMIT DETECTION
# ============================================================

def has_top_level_limit(sql: str) -> bool:
    """
    Basic LIMIT detection.

    If the generated SQL already contains a numeric LIMIT,
    preserve it.

    The outer execution layer still protects the maximum
    number of returned rows through max_rows.
    """

    lowered = remove_sql_comments(sql).lower()

    return bool(
        re.search(
            r"\blimit\s+\d+\b",
            lowered,
        )
    )


def apply_result_limit(
    sql: str,
    max_rows: int,
) -> str:
    """
    Apply a safe result limit when the AI query does not
    already specify one.
    """

    if max_rows < 1:
        max_rows = 1

    if max_rows > ABSOLUTE_MAX_ROWS:
        max_rows = ABSOLUTE_MAX_ROWS

    if has_top_level_limit(sql):
        return sql

    return (
        f"{sql}\n"
        f"LIMIT {max_rows}"
    )


# ============================================================
# COMPLETE VALIDATION PIPELINE
# ============================================================

def validate_read_only_sql(
    sql: str,
    allowed_tables: list[str],
) -> str:
    """
    Complete SQL safety validation.
    """

    sql = normalize_sql(sql)

    validate_single_statement(sql)

    validate_read_only_statement(sql)

    validate_forbidden_keywords(sql)

    validate_forbidden_functions(sql)

    validate_system_objects(sql)

    validate_workspace_tables(
        sql,
        allowed_tables,
    )

    return sql


# ============================================================
# SAFE EXECUTION
# ============================================================

def execute_sql(
    sql: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    timeout_ms: int = DEFAULT_QUERY_TIMEOUT_MS,
) -> list[dict[str, Any]]:
    """
    Execute validated read-only SQL with:

    - safe result limits
    - PostgreSQL statement timeout
    - transaction protection
    - SQLAlchemy exception handling
    """

    # --------------------------------------------------------
    # Normalize execution limits
    # --------------------------------------------------------

    if max_rows < 1:
        max_rows = 1

    if max_rows > ABSOLUTE_MAX_ROWS:
        max_rows = ABSOLUTE_MAX_ROWS

    if timeout_ms < 1000:
        timeout_ms = 1000

    if timeout_ms > MAX_QUERY_TIMEOUT_MS:
        timeout_ms = MAX_QUERY_TIMEOUT_MS

    # --------------------------------------------------------
    # Normalize SQL
    # --------------------------------------------------------

    sql = normalize_sql(sql)

    # --------------------------------------------------------
    # Apply result limit
    # --------------------------------------------------------

    safe_sql = apply_result_limit(
        sql,
        max_rows,
    )

    try:
        with engine.begin() as connection:

            # ------------------------------------------------
            # PostgreSQL statement timeout
            # ------------------------------------------------
            #
            # set_config() is used instead of directly trying
            # to bind a parameter inside SET LOCAL.
            #
            # The third argument TRUE means the setting is
            # local to the current transaction.
            #
            connection.execute(
                text(
                    "SELECT set_config("
                    "'statement_timeout', "
                    ":timeout_value, "
                    "true"
                    ")"
                ),
                {
                    "timeout_value": f"{timeout_ms}ms"
                },
            )

            # ------------------------------------------------
            # Execute the actual query
            # ------------------------------------------------

            result = connection.execute(
                text(safe_sql)
            )

            # ------------------------------------------------
            # Convert SQLAlchemy rows to dictionaries
            # ------------------------------------------------

            rows = result.mappings().all()

            return [
                {
                    str(key): value
                    for key, value in row.items()
                }
                for row in rows
            ]

    except SQLAlchemyError as exc:

        # ----------------------------------------------------
        # Server-side debugging
        # ----------------------------------------------------
        #
        # Do not expose raw database internals to the user,
        # but print the real error in the backend terminal.
        #

        print(
            "\n"
            "==================================================\n"
            "ALOKO BUSINESS AI — SQL EXECUTION ERROR\n"
            "=================================================="
        )

        print(
            f"SQL:\n{safe_sql}"
        )

        print(
            f"\nDATABASE ERROR:\n{exc}"
        )

        print(
            "==================================================\n"
        )

        raise RuntimeError(
            "SQL execution failed."
        ) from exc


# ============================================================
# RESULT SUMMARIZATION
# ============================================================

def summarize_results(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create a compact result summary for the Business AI layer.
    """

    if not rows:
        return {
            "row_count": 0,
            "columns": [],
            "rows": [],
        }

    columns = list(
        rows[0].keys()
    )

    # Keep the stored/returned preview manageable.
    preview_rows = rows[:100]

    return {
        "row_count": len(rows),
        "columns": columns,
        "rows": preview_rows,
    }


# ============================================================
# PUBLIC QUERY PIPELINE
# ============================================================

def run_safe_query(
    sql: str,
    allowed_tables: list[str],
    max_rows: int = DEFAULT_MAX_ROWS,
    timeout_ms: int = DEFAULT_QUERY_TIMEOUT_MS,
) -> dict[str, Any]:
    """
    Public Business AI SQL execution pipeline.

    Flow:

        AI SQL
          ↓
        Normalize
          ↓
        Read-only validation
          ↓
        Dangerous SQL detection
          ↓
        Workspace table validation
          ↓
        Safe execution
          ↓
        Result summary
    """

    # --------------------------------------------------------
    # Validate generated SQL
    # --------------------------------------------------------

    validated_sql = validate_read_only_sql(
        sql=sql,
        allowed_tables=allowed_tables,
    )

    # --------------------------------------------------------
    # Execute validated SQL
    # --------------------------------------------------------

    rows = execute_sql(
        sql=validated_sql,
        max_rows=max_rows,
        timeout_ms=timeout_ms,
    )

    # --------------------------------------------------------
    # Summarize results
    # --------------------------------------------------------

    summary = summarize_results(
        rows
    )

    # --------------------------------------------------------
    # Return structured Business AI result
    # --------------------------------------------------------

    return {
        "success": True,
        "sql": validated_sql,
        "rows": rows,
        "summary": summary,
        "limits": {
            "max_rows": min(
                max_rows,
                ABSOLUTE_MAX_ROWS,
            ),
            "timeout_ms": min(
                max(
                    timeout_ms,
                    1000,
                ),
                MAX_QUERY_TIMEOUT_MS,
            ),
        },
    }