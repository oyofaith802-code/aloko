import os
from io import BytesIO

from dotenv import load_dotenv

load_dotenv()


def get_elevenlabs_client():
    from elevenlabs.client import ElevenLabs

    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is missing from environment.")

    return ElevenLabs(api_key=api_key)


def clone_voice(name: str, audio_bytes: bytes) -> str:
    if not name.strip():
        raise ValueError("Voice name is required.")

    if not audio_bytes:
        raise ValueError("Audio file is empty.")

    client = get_elevenlabs_client()

    result = client.voices.ivc.create(
        name=name.strip(),
        files=[BytesIO(audio_bytes)],
    )

    return result.voice_id


def generate_cloned_speech(
    text: str,
    voice_id: str,
) -> bytes:
    if not text.strip():
        raise ValueError("Text is required.")

    if not voice_id:
        raise ValueError("Voice ID is required.")

    client = get_elevenlabs_client()

    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    return b"".join(audio)
