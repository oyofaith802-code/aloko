import requests


TRANSLATOR_URL = "http://127.0.0.1:8001"


def translate_text(
    text: str,
    from_language: str,
    to_language: str
):
    response = requests.post(
        f"{TRANSLATOR_URL}/translate",
        json={
            "text": text,
            "from_language": from_language,
            "to_language": to_language,
        },
        timeout=120,
    )

    if not response.ok:
        try:
            detail = response.json().get(
                "detail",
                "Translation service failed."
            )
        except Exception:
            detail = "Translation service failed."

        raise RuntimeError(detail)

    return response.json()


def transcribe_audio(audio_path: str):
    with open(audio_path, "rb") as audio_file:
        response = requests.post(
            f"{TRANSLATOR_URL}/transcribe",
            files={
                "audio": (
                    audio_file.name,
                    audio_file,
                    "application/octet-stream"
                )
            },
            timeout=300,
        )

    if not response.ok:
        try:
            detail = response.json().get(
                "detail",
                "Transcription service failed."
            )
        except Exception:
            detail = "Transcription service failed."

        raise RuntimeError(detail)

    return response.json()