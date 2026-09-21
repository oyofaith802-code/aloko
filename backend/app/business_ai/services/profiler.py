import json

import pandas as pd


def profile_dataset(
    dataframe: pd.DataFrame,
) -> dict:

    missing = {}

    for column in dataframe.columns:
        missing[str(column)] = int(
            dataframe[column].isna().sum()
        )

    numeric_stats = {}

    numeric_columns = dataframe.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:
        series = dataframe[column]

        numeric_stats[str(column)] = {
            "min": (
                None
                if series.dropna().empty
                else float(series.min())
            ),
            "max": (
                None
                if series.dropna().empty
                else float(series.max())
            ),
            "mean": (
                None
                if series.dropna().empty
                else float(series.mean())
            ),
            "median": (
                None
                if series.dropna().empty
                else float(series.median())
            ),
        }

    categorical_stats = {}

    categorical_columns = dataframe.select_dtypes(
        include=["object", "category", "bool"]
    ).columns

    for column in categorical_columns:
        series = dataframe[column]

        categorical_stats[str(column)] = {
            "unique_count": int(
                series.nunique(
                    dropna=True
                )
            ),
            "top_values": [
                {
                    "value": str(value),
                    "count": int(count),
                }
                for value, count in (
                    series
                    .value_counts(
                        dropna=True
                    )
                    .head(10)
                    .items()
                )
            ],
        }

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(
            len(dataframe.columns)
        ),
        "duplicate_rows": int(
            dataframe.duplicated().sum()
        ),
        "missing_values": missing,
        "numeric_statistics": numeric_stats,
        "categorical_statistics": categorical_stats,
    }


def profile_to_json(
    dataframe: pd.DataFrame,
) -> str:

    return json.dumps(
        profile_dataset(dataframe),
        default=str,
    )