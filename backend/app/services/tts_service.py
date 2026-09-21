import os
import uuid
import asyncio
import edge_tts

AUDIO_DIR = "storage/audio"


async def generate_speech(
    text: str,
    voice: str = "en-US-AriaNeural"
):
    os.makedirs(AUDIO_DIR, exist_ok=True)

    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(AUDIO_DIR, filename)

    communicate = edge_tts.Communicate(
        text,
        voice
    )

    await communicate.save(output_path)

    if not os.path.exists(output_path):
        raise RuntimeError("Audio generation failed")

    return output_path