import os
import uuid
import requests

from dotenv import load_dotenv

load_dotenv()

MODEL = "fal-ai/ai-avatar/single-text"


def generate_avatar_video(
    avatar_image_url: str,
    script: str,
    voice: str = "Sarah",
    prompt: str = "A person speaking naturally and clearly to the camera."
):
    if not avatar_image_url:
        raise ValueError("Avatar image URL is missing")

    import fal_client

    result = fal_client.subscribe(
        MODEL,
        arguments={
            "image_url": avatar_image_url,
            "text_input": script,
            "voice": voice,
            "prompt": prompt,
            "resolution": "480p",
            "acceleration": "regular"
        }
    )

    video_url = result["video"]["url"]

    os.makedirs("storage/videos", exist_ok=True)

    filename = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join("storage/videos", filename)

    response = requests.get(video_url, timeout=300)
    response.raise_for_status()

    with open(output_path, "wb") as video_file:
        video_file.write(response.content)

    return output_path
