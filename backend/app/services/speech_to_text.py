import os
from faster_whisper import WhisperModel


MODEL_SIZE = "base"

_model = None


def get_model():
    global _model

    if _model is None:
        _model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8"
        )

    return _model


def transcribe_audio(audio_path: str):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    model = get_model()

    segments, info = model.transcribe(
        audio_path,
        beam_size=5
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    ).strip()

    return {
        "text": text,
        "language": info.language,
        "language_probability": info.language_probability
    }