import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.translator_client import (
    transcribe_audio,
    translate_text
)
from app.services.tts_service import generate_speech


router = APIRouter(
    prefix="/translator",
    tags=["Voice Translator"]
)


UPLOAD_DIR = "storage/translator"
os.makedirs(UPLOAD_DIR, exist_ok=True)


ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
    "audio/mp4": ".m4a",
    "audio/ogg": ".ogg",
}


def get_audio_extension(content_type: str):
    """
    Handles MIME types such as:
    audio/webm
    audio/webm;codecs=opus
    audio/ogg;codecs=opus
    """

    if not content_type:
        return None

    base_type = content_type.lower().split(";")[0].strip()

    return ALLOWED_AUDIO_TYPES.get(base_type)

@router.get("/languages")
async def get_translator_languages():
    return {
        "languages": [
            {"code": "ar", "name": "Arabic"},
            {"code": "bn", "name": "Bengali"},
            {"code": "zh", "name": "Chinese"},
            {"code": "nl", "name": "Dutch"},
            {"code": "en", "name": "English"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "el", "name": "Greek"},
            {"code": "he", "name": "Hebrew"},
            {"code": "hi", "name": "Hindi"},
            {"code": "id", "name": "Indonesian"},
            {"code": "it", "name": "Italian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "ms", "name": "Malay"},
            {"code": "fa", "name": "Persian"},
            {"code": "pl", "name": "Polish"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "es", "name": "Spanish"},
            {"code": "sw", "name": "Swahili"},
            {"code": "tl", "name": "Tagalog"},
            {"code": "th", "name": "Thai"},
            {"code": "tr", "name": "Turkish"},
            {"code": "uk", "name": "Ukrainian"},
            {"code": "ur", "name": "Urdu"},
            {"code": "vi", "name": "Vietnamese"},
        ]
    }

@router.post("/transcribe")
async def transcribe_voice(
    audio: UploadFile = File(...)
):
    extension = get_audio_extension(
        audio.content_type
    )

    if not extension:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {audio.content_type}"
        )

    filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    try:
        # Save uploaded audio
        with open(file_path, "wb") as buffer:
            buffer.write(await audio.read())

        # Send audio to translator microservice
        result = transcribe_audio(file_path)

        return {
            "message": "Audio transcribed successfully",
            "text": result["text"],
            "language": result["language"],
            "language_probability": result[
                "language_probability"
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    finally:
        # Remove temporary uploaded audio
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/translate")
async def translate_voice_text(
    text: str,
    from_language: str,
    to_language: str
):
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty."
        )

    try:
        result = translate_text(
            text=text,
            from_language=from_language,
            to_language=to_language
        )

        return {
            "message": "Text translated successfully",
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/voice")
async def translate_voice(
    audio: UploadFile = File(...),
    to_language: str = "en",
    voice: str = "en-US-AriaNeural"
):
    extension = get_audio_extension(
        audio.content_type
    )

    if not extension:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {audio.content_type}"
        )

    filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    try:
        # ==========================================
        # 1. SAVE AUDIO
        # ==========================================

        with open(file_path, "wb") as buffer:
            buffer.write(await audio.read())


        # ==========================================
        # 2. SPEECH → TEXT
        # ==========================================

        transcription = transcribe_audio(
            file_path
        )

        source_text = transcription["text"]
        source_language = transcription["language"]

        if not source_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No speech was detected in the audio."
            )


        # ==========================================
        # 3. TRANSLATE
        # ==========================================

        translation_result = translate_text(
            text=source_text,
            from_language=source_language,
            to_language=to_language
        )

        translated_text = translation_result[
            "translated_text"
        ]


        # ==========================================
        # 4. GENERATE TARGET VOICE
        # ==========================================

        audio_path = await generate_speech(
            text=translated_text,
            voice=voice
        )

        audio_filename = os.path.basename(
            audio_path
        )


        # ==========================================
        # 5. RETURN RESULT
        # ==========================================

        return {
            "message": "Voice translated successfully",
            "source_text": source_text,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": to_language,
            "voice": voice,
            "audio_url": (
                f"/storage/audio/{audio_filename}"
            )
        }


    except HTTPException:
        raise


    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice translation failed: {str(e)}"
        )


    finally:
        # Always remove temporary uploaded audio
        if os.path.exists(file_path):
            os.remove(file_path)
