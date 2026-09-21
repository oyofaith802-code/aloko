from app.models.voice import Voice
from app.services.voice_clone_service import generate_cloned_speech


class PersonalVoiceError(Exception):
    """Raised when a personal voice cannot be generated."""


def is_personal_voice_ready(voice: Voice) -> bool:
    return (
        voice.voice_type == "custom"
        and voice.status == "ready"
        and bool(voice.provider_voice_id)
    )


def generate_personal_voice_speech(
    text: str,
    voice: Voice,
) -> bytes:
    """
    Generate speech using a user's personal cloned voice.
    """

    if not text or not text.strip():
        raise PersonalVoiceError(
            "Text is required for personal voice generation."
        )

    if not is_personal_voice_ready(voice):
        raise PersonalVoiceError(
            "This personal voice is not ready for speech generation."
        )

    provider_voice_id = voice.provider_voice_id

    if not provider_voice_id:
        raise PersonalVoiceError(
            "This personal voice has no provider voice ID."
        )

    try:
        audio_bytes = generate_cloned_speech(
            text=text.strip(),
            voice_id=provider_voice_id,
        )

        if not audio_bytes:
            raise PersonalVoiceError(
                "Personal voice provider returned no audio."
            )

        return audio_bytes

    except PersonalVoiceError:
        raise

    except Exception as exc:
        raise PersonalVoiceError(
            f"Personal voice generation failed: {str(exc)}"
        ) from exc