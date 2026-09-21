import os
from io import BytesIO

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY is missing from .env")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def clone_voice(name: str, audio_bytes: bytes) -> str:
    """
    Create a custom voice using the configured voice provider.

    Returns:
        Provider voice ID.
    """

    if not name.strip():
        raise ValueError("Voice name is required.")

    if not audio_bytes:
        raise ValueError("Audio file is empty.")

    result = client.voices.ivc.create(
        name=name.strip(),
        files=[
            BytesIO(audio_bytes)
        ],
    )

    return result.voice_id


def generate_cloned_speech(
    text: str,
    voice_id: str,
) -> bytes:
    """
    Generate speech using an existing custom voice.
    """

    if not text.strip():
        raise ValueError("Text is required.")

    if not voice_id:
        raise ValueError("Voice ID is required.")

    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    return b"".join(audio)