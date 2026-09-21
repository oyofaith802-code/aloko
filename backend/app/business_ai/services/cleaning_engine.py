from __future__ import annotations

from typing import Any

import pandas as pd


def _safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _detect_empty_columns(df: pd.DataFrame) -> list[str]:
    empty_columns = []

    for column in df.columns:
        series = df[column]

        if series.isna().all():
            empty_columns.append(str(column))
            continue

        if series.astype(str).str.strip().eq("").all():
            empty_columns.append(str(column))

    return empty_columns


def _detect_missing_values(
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    results = []

    total_rows = len(df)

    if total_rows == 0:
        return results

    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        if missing_count > 0:
            percentage = (
                missing_count / total_rows
            ) * 100

            results.append(
                {
                    "column": str(column),
                    "missing_count": missing_count,
                    "missing_percentage": round(
                        percentage,
                        2,
                    ),
                }
            )

    return sorted(
        results,
        key=lambda item: item["missing_count"],
        reverse=True,
    )


def _detect_duplicates(
    df: pd.DataFrame,
) -> dict[str, Any]:
    duplicate_count = int(
        df.duplicated().sum()
    )

    percentage = 0.0

    if len(df) > 0:
        percentage = (
            duplicate_count / len(df)
        ) * 100

    return {
        "duplicate_rows": duplicate_count,
        "duplicate_percentage": round(
            percentage,
            2,
        ),
    }


def _detect_constant_columns(
    df: pd.DataFrame,
) -> list[str]:
    constant_columns = []

    for column in df.columns:
        unique_count = df[column].nunique(
            dropna=False
        )

        if unique_count <= 1:
            constant_columns.append(
                str(column)
            )

    return constant_columns


def _detect_high_cardinality_columns(
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    results = []

    row_count = len(df)

    if row_count == 0:
        return results

    for column in df.columns:
        unique_count = int(
            df[column].nunique(
                dropna=True
            )
        )

        if unique_count == 0:
            continue

        ratio = unique_count / row_count

        if ratio >= 0.95:
            results.append(
                {
                    "column": str(column),
                    "unique_count": unique_count,
                    "uniqueness_ratio": round(
                        ratio,
                        4,
                    ),
                }
            )

    return results


def _detect_numeric_outliers(
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    results = []

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:
        series = df[column].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outlier_mask = (
            (series < lower_bound)
            | (series > upper_bound)
        )

        outlier_count = int(
            outlier_mask.sum()
        )

        if outlier_count > 0:
            results.append(
                {
                    "column": str(column),
                    "outlier_count": outlier_count,
                    "lower_bound": _safe_float(
                        lower_bound
                    ),
                    "upper_bound": _safe_float(
                        upper_bound
                    ),
                }
            )

    return sorted(
        results,
        key=lambda item: item["outlier_count"],
        reverse=True,
    )


def _detect_suspicious_text_columns(
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    results = []

    text_columns = df.select_dtypes(
        include=["object", "string", "category"]
    ).columns

    for column in text_columns:
        series = df[column].dropna().astype(str)

        if series.empty:
            continue

        whitespace_count = int(
            series.str.strip().eq("").sum()
        )

        leading_trailing_spaces = int(
            (series != series.str.strip()).sum()
        )

        if (
            whitespace_count > 0
            or leading_trailing_spaces > 0
        ):
            results.append(
                {
                    "column": str(column),
                    "blank_values": whitespace_count,
                    "values_with_extra_spaces": (
                        leading_trailing_spaces
                    ),
                }
            )

    return results


def _detect_possible_date_columns(
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    results = []

    for column in df.columns:
        name = str(column).lower()

        looks_like_date = any(
            keyword in name
            for keyword in [
                "date",
                "time",
                "timestamp",
                "created",
                "updated",
                "year",
            ]
        )

        if not looks_like_date:
            continue

        series = df[column]

        if pd.api.types.is_datetime64_any_dtype(
            series
        ):
            results.append(
                {
                    "column": str(column),
                    "detected": True,
                    "invalid_count": 0,
                }
            )
            continue

        parsed = pd.to_datetime(
            series,
            errors="coerce",
        )

        non_empty = series.notna()

        invalid_count = int(
            (
                non_empty
                & parsed.isna()
            ).sum()
        )

        results.append(
            {
                "column": str(column),
                "detected": True,
                "invalid_count": invalid_count,
            }
        )

    return results


def _build_recommendations(
    report: dict[str, Any],
) -> list[str]:
    recommendations = []

    if report["empty_columns"]:
        recommendations.append(
            "Review completely empty columns and remove them if they are not required."
        )

    if report["missing_values"]:
        recommendations.append(
            "Review missing values and determine whether to fill, exclude, or retain them."
        )

    if report["duplicates"]["duplicate_rows"] > 0:
        recommendations.append(
            "Investigate duplicate rows before using the dataset for business metrics."
        )

    if report["constant_columns"]:
        recommendations.append(
            "Review constant columns because they provide little analytical value."
        )

    if report["outliers"]:
        recommendations.append(
            "Review detected numeric outliers before making important business decisions."
        )

    if report["suspicious_text"]:
        recommendations.append(
            "Normalize text values by trimming unnecessary whitespace and checking category consistency."
        )

    invalid_dates = sum(
        item["invalid_count"]
        for item in report["date_columns"]
    )

    if invalid_dates > 0:
        recommendations.append(
            "Review invalid date/time values before performing time-based analysis."
        )

    if not recommendations:
        recommendations.append(
            "No major automatic data-quality issues were detected."
        )

    return recommendations


def analyze_data_quality(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """
    Perform industry-agnostic data-quality analysis.

    The engine does not assume a specific industry,
    dataset name, or column naming convention.
    """

    if dataframe is None:
        raise ValueError(
            "A dataframe is required."
        )

    df = dataframe.copy()

    report: dict[str, Any] = {
        "row_count": int(len(df)),
        "column_count": int(
            len(df.columns)
        ),
        "empty_columns": (
            _detect_empty_columns(df)
        ),
        "missing_values": (
            _detect_missing_values(df)
        ),
        "duplicates": (
            _detect_duplicates(df)
        ),
        "constant_columns": (
            _detect_constant_columns(df)
        ),
        "high_cardinality_columns": (
            _detect_high_cardinality_columns(df)
        ),
        "outliers": (
            _detect_numeric_outliers(df)
        ),
        "suspicious_text": (
            _detect_suspicious_text_columns(df)
        ),
        "date_columns": (
            _detect_possible_date_columns(df)
        ),
    }

    total_cells = (
        report["row_count"]
        * report["column_count"]
    )

    missing_cells = sum(
        item["missing_count"]
        for item in report["missing_values"]
    )

    if total_cells > 0:
        missing_ratio = (
            missing_cells / total_cells
        )
    else:
        missing_ratio = 0.0

    duplicate_ratio = (
        report["duplicates"][
            "duplicate_percentage"
        ]
        / 100
    )

    quality_penalty = (
        (missing_ratio * 40)
        + (duplicate_ratio * 30)
    )

    if report["empty_columns"]:
        quality_penalty += min(
            10,
            len(report["empty_columns"]) * 2,
        )

    if report["outliers"]:
        quality_penalty += min(
            10,
            len(report["outliers"]) * 1.5,
        )

    score = max(
        0.0,
        min(
            100.0,
            100.0 - quality_penalty,
        ),
    )

    report["data_quality_score"] = round(
        score,
        2,
    )

    report["recommendations"] = (
        _build_recommendations(report)
    )

    return report