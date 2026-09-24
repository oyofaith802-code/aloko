from pathlib import Path

from sqlalchemy import inspect, text

from app.database.connection import engine


def delete_dataset_storage(
    storage_path: str | None,
    table_name: str | None,
) -> None:
    """
    Remove the uploaded dataset file and generated PostgreSQL table.

    This helper only accepts the table name/path already stored on the
    authenticated user's BusinessDataset record.
    """

    # ------------------------------------------------------------
    # Delete generated PostgreSQL table
    # ------------------------------------------------------------
    if table_name:
        table_name = str(table_name).strip()

        if table_name:
            inspector = inspect(engine)

            if inspector.has_table(table_name):
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            f'DROP TABLE IF EXISTS "{table_name}"'
                        )
                    )

    # ------------------------------------------------------------
    # Delete uploaded file
    # ------------------------------------------------------------
    if storage_path:
        path = Path(storage_path)

        if path.exists() and path.is_file():
            path.unlink()
