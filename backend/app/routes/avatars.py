from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.avatar import Avatar
from app.models.user import User
from app.models.creator_scene import CreatorScene
from app.models.video import Video


# =========================================================
# ENABLE HEIC / HEIF SUPPORT
# =========================================================

register_heif_opener()


router = APIRouter(
    prefix="/avatars",
    tags=["Avatars"],
)


# =========================================================
# STORAGE
# =========================================================

STORAGE_DIR = Path("storage")
AVATAR_STORAGE_DIR = STORAGE_DIR / "avatars"

AVATAR_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# SETTINGS
# =========================================================

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# Large phone photos can be unnecessarily expensive for
# SadTalker. Keep the longest side within this limit.
MAX_IMAGE_DIMENSION = 2048


# =========================================================
# UPLOAD AVATAR
# =========================================================

@router.post("/upload")
async def upload_avatar(
    name: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a user's avatar image.

    Supports:
        JPG / JPEG
        PNG
        WEBP
        HEIC
        HEIF

    The uploaded image is decoded and normalized into a
    standard RGB JPEG so OpenCV and SadTalker can read it.
    """

    # -----------------------------------------------------
    # Validate avatar name
    # -----------------------------------------------------

    clean_name = name.strip()

    if not clean_name:
        raise HTTPException(
            status_code=400,
            detail="Avatar name is required.",
        )

    if len(clean_name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Avatar name must be 100 characters or less.",
        )

    # -----------------------------------------------------
    # Read uploaded image
    # -----------------------------------------------------

    image_data = await image.read()

    if not image_data:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty.",
        )

    if len(image_data) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Image must be 10 MB or smaller.",
        )

    # -----------------------------------------------------
    # Decode image using Pillow
    #
    # IMPORTANT:
    # We intentionally do NOT trust content_type here.
    #
    # Some phones upload HEIC files with a misleading MIME
    # type such as image/jpeg.
    # -----------------------------------------------------

    try:
        source_image = Image.open(BytesIO(image_data))

        # Force actual image decoding now.
        source_image.load()

    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file is not a supported image. "
                "Please upload JPG, PNG, WEBP, HEIC or HEIF."
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image could not be read.",
        ) from exc

    # -----------------------------------------------------
    # Check detected format
    # -----------------------------------------------------

    detected_format = (
        source_image.format.upper()
        if source_image.format
        else ""
    )

    allowed_formats = {
        "JPEG",
        "PNG",
        "WEBP",
        "HEIF",
        "HEIC",
    }

    if detected_format not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Please upload JPG, PNG, WEBP, HEIC or HEIF."
            ),
        )

    # -----------------------------------------------------
    # Normalize image
    #
    # RGB is important because:
    # - JPEG does not support RGBA
    # - SadTalker/OpenCV works reliably with standard RGB
    # -----------------------------------------------------

    try:
        normalized_image = source_image.convert("RGB")

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Failed to process the uploaded image.",
        ) from exc

    # -----------------------------------------------------
    # Resize very large images
    # -----------------------------------------------------

    width, height = normalized_image.size

    if max(width, height) > MAX_IMAGE_DIMENSION:
        normalized_image.thumbnail(
            (
                MAX_IMAGE_DIMENSION,
                MAX_IMAGE_DIMENSION,
            ),
            Image.Resampling.LANCZOS,
        )

    # -----------------------------------------------------
    # Generate unique JPEG filename
    # -----------------------------------------------------

    filename = f"{uuid4().hex}.jpg"

    file_path = AVATAR_STORAGE_DIR / filename

    # -----------------------------------------------------
    # Save normalized JPEG
    # -----------------------------------------------------

    try:
        normalized_image.save(
            file_path,
            format="JPEG",
            quality=95,
            optimize=True,
        )

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to save avatar image.",
        ) from exc

    # -----------------------------------------------------
    # URL saved in database
    # -----------------------------------------------------

    image_url = (
        f"/storage/avatars/{filename}"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Owner comes from JWT, NOT from frontend.
    # -----------------------------------------------------

    avatar = Avatar(
        user_id=current_user.id,
        name=clean_name,
        image_url=image_url,
    )

    # -----------------------------------------------------
    # Save database record
    # -----------------------------------------------------

    try:
        db.add(avatar)
        db.commit()
        db.refresh(avatar)

    except Exception as exc:
        db.rollback()

        # Remove image if database operation fails.
        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail="Failed to save avatar.",
        ) from exc

    return {
        "id": avatar.id,
        "name": avatar.name,
        "image_url": avatar.image_url,
        "format": "JPEG",
        "width": normalized_image.width,
        "height": normalized_image.height,
    }


# =========================================================
# GET MY AVATARS
# =========================================================

@router.get("/me")
def get_my_avatars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return only avatars belonging to the authenticated user.
    """

    avatars = (
        db.query(Avatar)
        .filter(
            Avatar.user_id == current_user.id
        )
        .order_by(
            Avatar.id.desc()
        )
        .all()
    )

    return [
        {
            "id": avatar.id,
            "name": avatar.name,
            "image_url": avatar.image_url,
        }
        for avatar in avatars
    ]



# =========================================================
# DELETE AVATAR
# =========================================================

@router.delete("/{avatar_id}")
def delete_avatar(
    avatar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    avatar = (
        db.query(Avatar)
        .filter(
            Avatar.id == avatar_id,
            Avatar.user_id == current_user.id,
        )
        .first()
    )

    if not avatar:
        raise HTTPException(
            status_code=404,
            detail="Avatar not found.",
        )

    scene_using_avatar = (
        db.query(CreatorScene)
        .filter(CreatorScene.avatar_id == avatar.id)
        .first()
    )

    if scene_using_avatar:
        raise HTTPException(
            status_code=409,
            detail=(
                "This avatar is currently used by a Creator Studio scene. "
                "Select another avatar for that scene before deleting it."
            ),
        )

    video_using_avatar = (
        db.query(Video)
        .filter(Video.avatar_id == avatar.id)
        .first()
    )

    if video_using_avatar:
        raise HTTPException(
            status_code=409,
            detail="This avatar is used by an existing video and cannot be deleted.",
        )

    image_url = avatar.image_url or ""

    if "/storage/" in image_url:
        relative_path = image_url.split("/storage/", 1)[1]
        file_path = STORAGE_DIR / Path(relative_path)
    else:
        file_path = Path(image_url)

    try:
        db.delete(avatar)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete avatar.",
        ) from exc

    try:
        file_path.resolve().unlink(missing_ok=True)
    except OSError:
        pass

    return {
        "message": "Avatar deleted successfully.",
        "id": avatar_id,
    }


# =========================================================
# GET SINGLE AVATAR
# =========================================================

@router.get("/{avatar_id}")
def get_avatar(
    avatar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return one avatar, but only when it belongs
    to the authenticated user.
    """

    avatar = (
        db.query(Avatar)
        .filter(
            Avatar.id == avatar_id,
            Avatar.user_id == current_user.id,
        )
        .first()
    )

    if not avatar:
        raise HTTPException(
            status_code=404,
            detail="Avatar not found.",
        )

    return {
        "id": avatar.id,
        "name": avatar.name,
        "image_url": avatar.image_url,
    }
