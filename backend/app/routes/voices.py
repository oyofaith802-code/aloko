import os
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.voice import Voice
from app.models.user import User
from app.services.tts_service import generate_speech
from app.services.voice_catalog import get_all_voices
from app.services.voice_clone_service import clone_voice
from app.core.security import get_current_user


router = APIRouter(
    prefix="/voices",
    tags=["Voices"],
)


# ============================================================
# STORAGE
# ============================================================

UPLOAD_DIR = Path("storage") / "voices"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# Maximum custom voice upload size: 25 MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024


# Supported audio file extensions
ALLOWED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".webm",
    ".ogg",
}


# ============================================================
# VOICE CATALOG
# ============================================================

@router.get("/catalog")
async def voice_catalog():
    """
    Public voice catalog.

    Only built-in/public voice information is returned.
    Private user voices are never exposed here.
    """

    voices = await get_all_voices()

    return {
        "count": len(voices),
        "voices": voices,
    }


# ============================================================
# VOICE LANGUAGES
# ============================================================

@router.get("/languages")
async def voice_languages():
    """
    Return languages available in the public voice catalog.
    """

    voices = await get_all_voices()

    languages = sorted(
        set(
            voice["language"]
            for voice in voices
            if voice.get("language")
        )
    )

    return {
        "count": len(languages),
        "languages": languages,
    }


# ============================================================
# FILTERED VOICE LIST
# ============================================================

@router.get("/list")
async def voice_list(
    language: str | None = None,
    country: str | None = None,
    gender: str | None = None,
):
    """
    Filter the public voice catalog.
    """

    voices = await get_all_voices()

    if language:
        language_lower = language.lower()

        voices = [
            voice
            for voice in voices
            if voice.get("language", "").lower()
            == language_lower
        ]

    if country:
        country_lower = country.lower()

        voices = [
            voice
            for voice in voices
            if voice.get("country", "").lower()
            == country_lower
        ]

    if gender:
        gender_lower = gender.lower()

        voices = [
            voice
            for voice in voices
            if voice.get("gender", "").lower()
            == gender_lower
        ]

    return {
        "count": len(voices),
        "voices": voices,
    }


# ============================================================
# AI VOICE GENERATION
# ============================================================

class VoiceGenerate(BaseModel):
    """
    Request body for built-in AI voice generation.

    User identity comes from the JWT.
    """

    text: str
    voice: str


@router.post("/generate")
async def generate_voice(
    data: VoiceGenerate,
    current_user: User = Depends(get_current_user),
):
    """
    Generate speech using a built-in Aloko voice.
    """

    # --------------------------------------------------------
    # VALIDATE TEXT
    # --------------------------------------------------------

    text = data.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    if len(text) > 5000:
        raise HTTPException(
            status_code=400,
            detail=(
                "Text is too long. "
                "Maximum 5000 characters."
            ),
        )

    # --------------------------------------------------------
    # VALIDATE VOICE
    # --------------------------------------------------------

    voice_name = data.voice.strip()

    if not voice_name:
        raise HTTPException(
            status_code=400,
            detail="Voice must be selected.",
        )

    voices = await get_all_voices()

    selected_voice = next(
        (
            voice
            for voice in voices
            if voice.get("tts_voice") == voice_name
        ),
        None,
    )

    if not selected_voice:
        raise HTTPException(
            status_code=400,
            detail="Invalid voice selected.",
        )

    # --------------------------------------------------------
    # GENERATE SPEECH
    # --------------------------------------------------------

    try:
        audio_path = await generate_speech(
            text=text,
            voice=selected_voice["tts_voice"],
        )

        filename = os.path.basename(audio_path)

        audio_url = (
            f"/storage/audio/{filename}"
        )

        return {
            "message": "Voice generated successfully",

            "voice_id": selected_voice.get(
                "id"
            ),

            "voice_name": selected_voice.get(
                "name"
            ),

            "language": selected_voice.get(
                "language"
            ),

            "language_code": selected_voice.get(
                "language_code"
            ),

            "country": selected_voice.get(
                "country"
            ),

            "accent": selected_voice.get(
                "accent"
            ),

            "gender": selected_voice.get(
                "gender"
            ),

            "audio_url": audio_url,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Voice generation failed: {str(exc)}"
            ),
        ) from exc


# ============================================================
# CUSTOM / PERSONAL VOICE UPLOAD
# ============================================================

@router.post("/upload")
async def upload_voice(
    name: str = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a user's personal voice recording to the Aloko voice library."""

    clean_name = name.strip() or "My Personal Voice"

    if len(clean_name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Voice name must be 100 characters or less.",
        )

    original_filename = audio.filename or ""

    if not original_filename.strip():
        raise HTTPException(
            status_code=400,
            detail="Audio filename is required.",
        )

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Supported formats: MP3, WAV, M4A, AAC, WEBM and OGG."
            ),
        )

    try:
        file_data = await audio.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Failed to read uploaded audio.",
        ) from exc

    if not file_data:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty.",
        )

    if len(file_data) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio file must be 25 MB or smaller.",
        )

    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename
    audio_url = f"/storage/voices/{filename}"

    try:
        file_path.write_bytes(file_data)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to save audio file.",
        ) from exc

    # Save the recording first.
    # Provider cloning must never prevent the recording from being saved.
    provider_voice_id = None
    voice_status = "recorded"
    cloning_message = "Voice recording saved successfully."

    try:
        provider_voice_id = clone_voice(
            name=clean_name,
            audio_bytes=file_data,
        )

        if provider_voice_id:
            voice_status = "ready"
            cloning_message = "Personal voice saved and cloned successfully."

    except Exception:
        # Keep the user's recording even when the provider rejects cloning.
        provider_voice_id = None
        voice_status = "recorded"
        cloning_message = (
            "Personal voice recording saved successfully. "
            "AI voice cloning is not currently available for this voice."
        )

    voice = Voice(
        user_id=current_user.id,
        name=clean_name,
        voice_type="custom",
        audio_url=audio_url,
        provider_voice_id=provider_voice_id,
        status=voice_status,
    )

    try:
        db.add(voice)
        db.commit()
        db.refresh(voice)
    except Exception as exc:
        db.rollback()

        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail="Failed to save custom voice.",
        ) from exc

    return {
        "message": cloning_message,
        "voice_id": voice.id,
        "user_id": voice.user_id,
        "name": voice.name,
        "voice_type": voice.voice_type,
        "status": voice.status,
        "provider_voice_id": voice.provider_voice_id,
        "audio_url": voice.audio_url,
        "cloning_available": bool(provider_voice_id),
    }

# ============================================================
# GET SINGLE CUSTOM VOICE
# ============================================================

@router.get("/me/{voice_id}")
def get_my_voice(
    voice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get one custom voice only when it belongs
    to the authenticated user.
    """

    voice = (
        db.query(Voice)
        .filter(
            Voice.id == voice_id,
            Voice.user_id == current_user.id,
        )
        .first()
    )

    if not voice:
        raise HTTPException(
            status_code=404,
            detail="Voice not found.",
        )

    return {
        "id": voice.id,

        "name": voice.name,

        "voice_type": voice.voice_type,

        "audio_url": voice.audio_url,

        "provider_voice_id": (
            voice.provider_voice_id
        ),

        "status": voice.status,

        "created_at": voice.created_at,
    }


# ============================================================
# DELETE MY CUSTOM VOICE
# ============================================================

@router.delete("/me/{voice_id}")
def delete_my_voice(
    voice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a custom voice belonging to the
    authenticated user.
    """

    # --------------------------------------------------------
    # FIND OWNED VOICE
    # --------------------------------------------------------

    voice = (
        db.query(Voice)
        .filter(
            Voice.id == voice_id,
            Voice.user_id == current_user.id,
        )
        .first()
    )

    if not voice:
        raise HTTPException(
            status_code=404,
            detail="Voice not found.",
        )

    # --------------------------------------------------------
    # DELETE LOCAL AUDIO FILE
    # --------------------------------------------------------

    if voice.audio_url:

        filename = Path(
            voice.audio_url
        ).name

        file_path = (
            UPLOAD_DIR / filename
        )

        try:
            file_path.unlink(
                missing_ok=True
            )

        except OSError:
            pass

    # --------------------------------------------------------
    # DELETE DATABASE RECORD
    # --------------------------------------------------------

    try:
        db.delete(voice)
        db.commit()

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to delete voice.",
        ) from exc

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "message": "Voice deleted successfully.",
        "voice_id": voice_id,
    }
