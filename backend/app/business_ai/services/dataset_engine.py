import re
import uuid
from pathlib import Path

import pandas as pd
from sqlalchemy import inspect

from app.database.connection import engine
from app.business_ai.extractors.pdf_extractor import extract_pdf
from app.business_ai.extractors.docx_extractor import extract_docx


BASE_STORAGE_DIR = Path("storage") / "business_datasets"
BASE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


ALLOWED_EXTENSIONS = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".pdf": "pdf",
    ".docx": "docx",
}


def get_source_type(filename: str) -> str:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. "
            "Supported formats: CSV, XLSX, XLS, PDF and DOCX."
        )

    return ALLOWED_EXTENSIONS[extension]


def generate_table_name(workspace_id: int) -> str:
    unique_id = uuid.uuid4().hex[:12]

    return f"biz_ws_{workspace_id}_{unique_id}"


def save_uploaded_file(
    file_bytes: bytes,
    filename: str,
    workspace_id: int,
) -> Path:

    workspace_dir = BASE_STORAGE_DIR / str(workspace_id)

    workspace_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_name = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        filename,
    )

    unique_name = (
        f"{uuid.uuid4().hex[:8]}_{safe_name}"
    )

    destination = workspace_dir / unique_name

    destination.write_bytes(file_bytes)

    return destination


def load_dataset(
    file_path: Path,
    source_type: str,
) -> pd.DataFrame:

    if source_type == "csv":
        return pd.read_csv(file_path)

    if source_type in {"xlsx", "xls"}:
        return pd.read_excel(
            file_path,
            sheet_name=0,
        )

    raise ValueError(
        "This file type is not a tabular dataset."
    )


def extract_document(
    file_path: Path,
    source_type: str,
) -> dict:

    if source_type == "pdf":
        return extract_pdf(file_path)

    if source_type == "docx":
        return extract_docx(file_path)

    raise ValueError(
        "Document extraction is only supported for PDF and DOCX."
    )


def create_database_table(
    dataframe: pd.DataFrame,
    table_name: str,
) -> int:

    dataframe.to_sql(
        name=table_name,
        con=engine,
        if_exists="fail",
        index=False,
    )

    return len(dataframe)


def table_exists(
    table_name: str,
) -> bool:

    inspector = inspect(engine)

    return inspector.has_table(
        table_name
    )