import os
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.video import Video
from app.models.avatar import Avatar
from app.models.voice import Voice
from app.models.user import User

from app.services.tts_service import generate_speech
from app.services.sadtalker_service import (
    generate_sadtalker_video,
)
from app.services.voice_catalog import get_all_voices

from app.core.security import get_current_user


router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
)


# ============================================================
# STORAGE
# ============================================================

STORAGE_DIR = Path("storage")
AVATAR_STORAGE_DIR = STORAGE_DIR / "avatars"
VIDEO_STORAGE_DIR = STORAGE_DIR / "videos"
AUDIO_STORAGE_DIR = STORAGE_DIR / "audio"

VIDEO_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

AUDIO_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# VIDEO REQUEST
# ============================================================

class VideoCreate(BaseModel):
    """
    Video generation request.

    IMPORTANT:
    user_id is intentionally NOT accepted.

    The authenticated user comes from the JWT.
    """

    avatar_id: int
    voice_id: int | None = None
    voice: str | None = None
    script: str


# ============================================================
# HELPER: AVATAR URL -> LOCAL FILE
# ============================================================

def get_avatar_file_path(
    image_url: str,
) -> str:
    """
    Convert an avatar storage URL such as:

        /storage/avatars/example.jpg

    into the local filesystem path:

        storage/avatars/example.jpg
    """

    if not image_url:
        raise HTTPException(
            status_code=404,
            detail="Avatar image path is missing.",
        )

    normalized = image_url.replace(
        "\\",
        "/",
    )

    prefix = "/storage/"

    if normalized.startswith(prefix):
        relative_path = normalized[
            len(prefix):
        ]

        file_path = (
            STORAGE_DIR /
            Path(relative_path)
        )

    else:
        # Compatibility with older records that may
        # contain a filesystem path.
        file_path = Path(
            image_url
        )

    file_path = file_path.resolve()

    storage_root = STORAGE_DIR.resolve()

    # Security: don't allow an avatar database value
    # to escape the storage directory.
    try:
        file_path.relative_to(
            storage_root
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid avatar file path.",
        ) from exc

    return str(file_path)


# ============================================================
# GENERATE AI VIDEO
# ============================================================

@router.post("/generate")
async def generate_video(
    data: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a talking-avatar video.

    Ownership is always determined from the authenticated
    user's JWT.
    """

    # ========================================================
    # VALIDATE SCRIPT
    # ========================================================

    script = data.script.strip()

    if not script:
        raise HTTPException(
            status_code=400,
            detail="Script cannot be empty.",
        )

    if len(script) > 5000:
        raise HTTPException(
            status_code=400,
            detail=(
                "Script is too long. "
                "Maximum 5000 characters."
            ),
        )

    # ========================================================
    # FIND AVATAR
    # ========================================================
    # CRITICAL SECURITY CHECK:
    #
    # The avatar must belong to the authenticated user.
    # We NEVER trust a user_id from the browser.
    # ========================================================

    avatar = (
        db.query(Avatar)
        .filter(
            Avatar.id == data.avatar_id,
            Avatar.user_id == current_user.id,
        )
        .first()
    )

    if not avatar:
        raise HTTPException(
            status_code=404,
            detail="Avatar not found.",
        )

    # ========================================================
    # GET LOCAL AVATAR FILE
    # ========================================================

    avatar_path = get_avatar_file_path(
        avatar.image_url
    )

    if not os.path.exists(avatar_path):
        raise HTTPException(
            status_code=404,
            detail="Avatar image file not found.",
        )

    # ========================================================
    # FIND SELECTED VOICE
    # ========================================================

    selected_voice = None
    custom_voice = None

    # ========================================================
    # BUILT-IN ALOKO VOICE
    # ========================================================

    if data.voice:
        requested_voice = data.voice.strip()

        if requested_voice:
            voices = await get_all_voices()

            selected_voice = next(
                (
                    voice
                    for voice in voices
                    if voice.get("tts_voice")
                    == requested_voice
                ),
                None,
            )

            if not selected_voice:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid built-in voice selected."
                    ),
                )

    # ========================================================
    # CUSTOM USER VOICE
    # ========================================================

    elif data.voice_id is not None:

        custom_voice = (
            db.query(Voice)
            .filter(
                Voice.id == data.voice_id,
                Voice.user_id == current_user.id,
            )
            .first()
        )

        if not custom_voice:
            raise HTTPException(
                status_code=404,
                detail="Voice not found.",
            )

        if custom_voice.voice_type != "custom":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Selected voice is not a custom voice."
                ),
            )

        # ----------------------------------------------------
        # CUSTOM VOICE CLONING NOT CONNECTED YET
        # ----------------------------------------------------

        raise HTTPException(
            status_code=501,
            detail=(
                "Custom voice cloning is not connected "
                "to the video generator yet. "
                "Please select a built-in voice."
            ),
        )

    # ========================================================
    # DEFAULT BUILT-IN VOICE
    # ========================================================

    else:
        selected_voice = {
            "tts_voice": "en-US-AriaNeural",
            "name": "Aria",
            "language": "en",
            "language_code": "en-US",
            "country": "US",
            "accent": "en-US",
            "gender": "female",
        }

    # ========================================================
    # FINAL VOICE CHECK
    # ========================================================

    if not selected_voice:
        raise HTTPException(
            status_code=400,
            detail="Please select a valid voice.",
        )

    # ========================================================
    # CREATE DATABASE RECORD
    # ========================================================
    #
    # Ownership comes from current_user.id.
    # ========================================================

    video = Video(
        user_id=current_user.id,
        avatar_id=avatar.id,
        voice_id=data.voice_id,
        script=script,
        status="processing",
    )

    try:
        db.add(video)
        db.commit()
        db.refresh(video)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create video record.",
        ) from exc

    # ========================================================
    # GENERATION
    # ========================================================

    try:

        # ====================================================
        # GENERATE AUDIO
        # ====================================================

        audio_path = await generate_speech(
            text=script,
            voice=selected_voice["tts_voice"],
        )

        if not audio_path:
            raise RuntimeError(
                "The speech service did not return an audio file."
            )

        audio_path = os.path.abspath(
            audio_path
        )

        if not os.path.exists(audio_path):
            raise RuntimeError(
                "Generated audio file was not found."
            )

        # ====================================================
        # GENERATE SADTALKER VIDEO
        # ====================================================

        output_path = generate_sadtalker_video(
            source_image=avatar_path,
            driven_audio=audio_path,
        )

        if not output_path:
            raise RuntimeError(
                "SadTalker did not return a video file."
            )

        output_path = os.path.abspath(
            output_path
        )

        if not os.path.exists(output_path):
            raise RuntimeError(
                "Generated video file was not found."
            )

        # ====================================================
        # VIDEO URL
        # ====================================================

        filename = os.path.basename(
            output_path
        )

        video_url = (
            f"/storage/videos/{filename}"
        )

        audio_filename = os.path.basename(
            audio_path
        )

        audio_url = (
            f"/storage/audio/{audio_filename}"
        )

        # ====================================================
        # SAVE RESULT
        # ====================================================

        video.video_url = video_url
        video.status = "completed"

        db.commit()
        db.refresh(video)

        # ====================================================
        # RESPONSE
        # ====================================================

        return {
            "message": (
                "AI video generated successfully"
            ),

            "video_id": video.id,

            "user_id": video.user_id,

            "avatar_id": video.avatar_id,

            "status": video.status,

            "voice": selected_voice[
                "tts_voice"
            ],

            "voice_name": selected_voice.get(
                "name"
            ),

            "audio_url": audio_url,

            "video_url": video_url,
        }

    except HTTPException:
        video.status = "failed"
        db.commit()
        raise

    except Exception as exc:

        # ====================================================
        # MARK VIDEO FAILED
        # ====================================================

        video.status = "failed"

        try:
            db.commit()
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Video generation failed: {str(exc)}"
            ),
        ) from exc


# ============================================================
# GET MY VIDEOS
# ============================================================

@router.get("/me")
def get_my_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return only videos belonging to the authenticated user.
    """

    videos = (
        db.query(Video)
        .filter(
            Video.user_id == current_user.id
        )
        .order_by(
            Video.id.desc()
        )
        .all()
    )

    return [
        {
            "id": video.id,
            "avatar_id": video.avatar_id,
            "voice_id": video.voice_id,
            "script": video.script,
            "status": video.status,
            "video_url": video.video_url,
        }
        for video in videos
    ]


# ============================================================
# GET SINGLE VIDEO
# ============================================================

@router.get("/me/{video_id}")
def get_my_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return one video only when it belongs
    to the authenticated user.
    """

    video = (
        db.query(Video)
        .filter(
            Video.id == video_id,
            Video.user_id == current_user.id,
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found.",
        )

    return {
        "id": video.id,
        "avatar_id": video.avatar_id,
        "voice_id": video.voice_id,
        "script": video.script,
        "status": video.status,
        "video_url": video.video_url,
    }