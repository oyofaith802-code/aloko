import json
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models.user import User

from app.business_ai.models import (
    BusinessDataset,
    BusinessWorkspace,
)

from app.business_ai.services.dataset_engine import (
    create_database_table,
    extract_document,
    generate_table_name,
    get_source_type,
    load_dataset,
    save_uploaded_file,
)

from app.business_ai.services.schema_engine import (
    build_schema,
)

from app.business_ai.services.profiler import (
    profile_dataset,
)

from app.business_ai.services.cleaning_engine import (
    analyze_data_quality,
)


MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
MAX_TABULAR_ROWS = 300_000

router = APIRouter(
    prefix="/business/datasets",
    tags=["Business AI - Datasets"],
)


@router.post("/upload")
async def upload_dataset(
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = (
        db.query(BusinessWorkspace)
        .filter(
            BusinessWorkspace.id == workspace_id,
            BusinessWorkspace.user_id == current_user.id,
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Business workspace not found.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    try:
        source_type = get_source_type(
            file.filename
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # ---------------------------------------------------------
    # UPLOAD SIZE LIMIT
    # ---------------------------------------------------------
    file_bytes = bytearray()

    while True:
        chunk = await file.read(1024 * 1024)

        if not chunk:
            break

        file_bytes.extend(chunk)

        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File is too large. Business AI allows "
                    f"maximum {MAX_UPLOAD_SIZE_MB} MB per file."
                ),
            )

    file_bytes = bytes(file_bytes)

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    try:
        print(f'[BUSINESS UPLOAD] filename={file.filename!r} source_type={source_type!r} content_type={file.content_type!r} size={len(file_bytes)}')
        storage_path = save_uploaded_file(
            file_bytes=file_bytes,
            filename=file.filename,
            workspace_id=workspace.id,
        )

        # ---------------------------------------------------------
        # DOCUMENT INGESTION
        # ---------------------------------------------------------
        if source_type in {"pdf", "docx"}:
            document = extract_document(
                storage_path,
                source_type,
            )

            document_text = document.get(
                "text",
                "",
            )

            if not document_text.strip() and not document.get(
                "tables"
            ):
                raise ValueError(
                    "No readable content was found in the document."
                )

            dataset = BusinessDataset(
                workspace_id=workspace.id,
                user_id=current_user.id,
                name=Path(
                    file.filename
                ).stem,
                original_filename=file.filename,
                source_type=source_type,
                storage_path=str(
                    storage_path
                ),
                table_name=None,
                row_count=None,
                schema_json=json.dumps(
                    {
                        "document": True,
                        "page_count": document.get(
                            "page_count"
                        ),
                        "paragraph_count": document.get(
                            "paragraph_count"
                        ),
                        "has_tables": bool(
                            document.get("tables")
                        ),
                    },
                    default=str,
                ),
                profile_json=json.dumps(
                    {
                        "document_text_length": len(
                            document_text
                        ),
                        "table_count": len(
                            document.get(
                                "tables",
                                []
                            )
                        ),
                    },
                    default=str,
                ),
                status="ready",
            )

            db.add(dataset)
            db.commit()
            db.refresh(dataset)

            return {
                "success": True,
                "message": (
                    "Document uploaded and "
                    "extracted successfully."
                ),
                "dataset": {
                    "id": dataset.id,
                    "workspace_id": dataset.workspace_id,
                    "name": dataset.name,
                    "original_filename": (
                        dataset.original_filename
                    ),
                    "source_type": dataset.source_type,
                    "table_name": dataset.table_name,
                    "row_count": dataset.row_count,
                    "schema": json.loads(
                        dataset.schema_json
                    ),
                    "profile": json.loads(
                        dataset.profile_json
                    ),
                    "document": {
                        "text": document.get(
                            "text",
                            "",
                        ),
                        "pages": document.get(
                            "pages",
                            [],
                        ),
                        "paragraphs": document.get(
                            "paragraphs",
                            [],
                        ),
                        "tables": document.get(
                            "tables",
                            [],
                        ),
                    },
                    "status": dataset.status,
                    "created_at": (
                        dataset.created_at
                    ),
                },
            }

        # ---------------------------------------------------------
        # TABULAR DATASET INGESTION
        # ---------------------------------------------------------
        dataframe = load_dataset(
            storage_path,
            source_type,
        )

        if len(dataframe.columns) == 0:
            raise ValueError(
                "The dataset has no columns."
            )

        if len(dataframe) == 0:
            raise ValueError(
                "The dataset contains no rows."
            )

        if len(dataframe) > MAX_TABULAR_ROWS:
            raise HTTPException(
                status_code=413,
                detail=(
                    "This dataset contains too many rows. "
                    "Business AI allows a maximum of "
                    f"{MAX_TABULAR_ROWS:,} rows for CSV, XLS, "
                    "and XLSX files."
                ),
            )

        # ---------------------------------------------------------
        # DATABASE TABLE
        # ---------------------------------------------------------
        table_name = generate_table_name(
            workspace.id
        )

        row_count = create_database_table(
            dataframe,
            table_name,
        )

        # ---------------------------------------------------------
        # SCHEMA
        # ---------------------------------------------------------
        schema = build_schema(
            dataframe
        )

        # ---------------------------------------------------------
        # PROFILE
        # ---------------------------------------------------------
        profile = profile_dataset(
            dataframe
        )

        # ---------------------------------------------------------
        # DATA QUALITY / CLEANING INTELLIGENCE
        # ---------------------------------------------------------
        data_quality = analyze_data_quality(
            dataframe
        )

        # Add cleaning intelligence to profile.
        profile["data_quality"] = data_quality

        # ---------------------------------------------------------
        # SAVE DATASET
        # ---------------------------------------------------------
        dataset = BusinessDataset(
            workspace_id=workspace.id,
            user_id=current_user.id,
            name=Path(
                file.filename
            ).stem,
            original_filename=file.filename,
            source_type=source_type,
            storage_path=str(
                storage_path
            ),
            table_name=table_name,
            row_count=row_count,
            schema_json=json.dumps(
                schema,
                default=str,
            ),
            profile_json=json.dumps(
                profile,
                default=str,
            ),
            status="ready",
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return {
            "success": True,
            "message": (
                "Dataset uploaded, profiled, "
                "and quality-analyzed successfully."
            ),
            "dataset": {
                "id": dataset.id,
                "workspace_id": dataset.workspace_id,
                "name": dataset.name,
                "original_filename": (
                    dataset.original_filename
                ),
                "source_type": dataset.source_type,
                "table_name": dataset.table_name,
                "row_count": dataset.row_count,
                "schema": schema,
                "profile": profile,
                "data_quality": data_quality,
                "status": dataset.status,
                "created_at": (
                    dataset.created_at
                ),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Dataset processing failed: "
                f"{str(exc)}"
            ),
        )


@router.get("")
def list_datasets(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = (
        db.query(BusinessWorkspace)
        .filter(
            BusinessWorkspace.id == workspace_id,
            BusinessWorkspace.user_id == current_user.id,
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Business workspace not found.",
        )

    datasets = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.workspace_id
            == workspace.id,
            BusinessDataset.user_id
            == current_user.id,
        )
        .order_by(
            BusinessDataset.created_at.desc()
        )
        .all()
    )

    return {
        "success": True,
        "datasets": [
            {
                "id": dataset.id,
                "name": dataset.name,
                "original_filename": (
                    dataset.original_filename
                ),
                "source_type": dataset.source_type,
                "table_name": dataset.table_name,
                "row_count": dataset.row_count,
                "status": dataset.status,
                "created_at": (
                    dataset.created_at
                ),
            }
            for dataset in datasets
        ],
    }


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = (
        db.query(BusinessDataset)
        .filter(
            BusinessDataset.id == dataset_id,
            BusinessDataset.user_id
            == current_user.id,
        )
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Business dataset not found.",
        )

    schema = (
        json.loads(dataset.schema_json)
        if dataset.schema_json
        else {}
    )

    profile = (
        json.loads(dataset.profile_json)
        if dataset.profile_json
        else {}
    )

    return {
        "success": True,
        "dataset": {
            "id": dataset.id,
            "workspace_id": dataset.workspace_id,
            "name": dataset.name,
            "original_filename": (
                dataset.original_filename
            ),
            "source_type": dataset.source_type,
            "table_name": dataset.table_name,
            "row_count": dataset.row_count,
            "schema": schema,
            "profile": profile,
            "data_quality": profile.get(
                "data_quality",
                {},
            ),
            "status": dataset.status,
            "created_at": dataset.created_at,
        },
    }