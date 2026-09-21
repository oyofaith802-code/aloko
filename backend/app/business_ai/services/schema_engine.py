import json

import pandas as pd


def build_schema(dataframe: pd.DataFrame) -> dict:
    columns = []

    for column in dataframe.columns:
        series = dataframe[column]

        columns.append(
            {
                "name": str(column),
                "dtype": str(series.dtype),
                "nullable": bool(series.isna().any()),
                "unique_count": int(
                    series.nunique(
                        dropna=True
                    )
                ),
            }
        )

    return {
        "column_count": len(dataframe.columns),
        "columns": columns,
    }


def schema_to_json(
    dataframe: pd.DataFrame,
) -> str:

    return json.dumps(
        build_schema(dataframe),
        default=str,
    )