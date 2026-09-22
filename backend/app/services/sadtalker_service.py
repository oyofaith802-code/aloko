import os
# app/services/sadtalker_service.py

import shutil
import subprocess
import urllib.request
import json
import time
import uuid
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(
    os.getenv(
        "ALOKO_BACKEND_DIR",
        str(Path(__file__).resolve().parents[2]),
    )
)

SADTALKER_DIR = Path(
    os.getenv(
        "SADTALKER_DIR",
        str(BACKEND_DIR.parent / "SadTalker"),
    )
)

SADTALKER_PYTHON = Path(
    os.getenv(
        "SADTALKER_PYTHON",
        r"C:\Users\USER\anaconda3\envs\sadtalker\python.exe",
    )
)
INFERENCE_SCRIPT = (
    SADTALKER_DIR / "inference.py"
)

RESULTS_DIR = (
    SADTALKER_DIR / "results"
)

STORAGE_DIR = (
    BACKEND_DIR / "storage"
)

AUDIO_STORAGE_DIR = (
    STORAGE_DIR / "audio"
)

VIDEO_STORAGE_DIR = (
    STORAGE_DIR / "videos"
)

FFMPEG_PATH = Path(
    os.getenv(
        "FFMPEG_PATH",
        r"C:\Users\USER\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build-shared\bin\ffmpeg.exe",
    )
)

# ============================================================
# CREATE DIRECTORIES
# ============================================================

AUDIO_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

VIDEO_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# VALIDATION HELPERS
# ============================================================

def validate_file(
    file_path: str | Path,
    description: str,
) -> Path:

    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"{description} not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"{description} is not a file: {path}"
        )

    return path


def validate_dependencies():
    """
    Make sure all required SadTalker dependencies
    exist before attempting generation.
    """

    validate_file(
        SADTALKER_PYTHON,
        "SadTalker Python executable",
    )

    validate_file(
        INFERENCE_SCRIPT,
        "SadTalker inference.py",
    )

    validate_file(
        FFMPEG_PATH,
        "FFmpeg executable",
    )

    SADTALKER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# WAV CONVERSION
# ============================================================

def convert_audio_to_wav(
    audio_path: str | Path,
) -> str:

    source_audio = validate_file(
        audio_path,
        "Input audio",
    )

    if source_audio.suffix.lower() == ".wav":
        return str(source_audio)

    output_path = (
        AUDIO_STORAGE_DIR
        / f"{uuid.uuid4()}_sadtalker.wav"
    )

    command = [
        str(FFMPEG_PATH),
        "-y",
        "-i",
        str(source_audio),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    print()
    print("========================================")
    print("Converting audio for SadTalker")
    print("========================================")
    print(f"Input:  {source_audio}")
    print(f"Output: {output_path}")
    print()

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        print("FFmpeg audio conversion failed.")
        print(result.stderr)

        raise RuntimeError(
            "Failed to convert audio for SadTalker.\n\n"
            f"{result.stderr[-5000:]}"
        )

    if not output_path.exists():
        raise RuntimeError(
            "Audio conversion completed but "
            "the WAV file was not created."
        )

    if output_path.stat().st_size == 0:
        raise RuntimeError(
            "Converted WAV file is empty."
        )

    return str(output_path)


# ============================================================
# FIND NEW SADTALKER VIDEO
# ============================================================

def find_new_sadtalker_video(
    existing_files: set[Path],
) -> Path | None:

    mp4_files = list(
        RESULTS_DIR.glob("*.mp4")
    )

    new_files = [
        path
        for path in mp4_files
        if path not in existing_files
    ]

    if not new_files:
        return None

    new_files.sort(
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    return new_files[0]


# ============================================================
# MAIN SADTALKER FUNCTION
# ============================================================


def generate_sadtalker_video(
    image_path: str,
    audio_path: str,
) -> str:

    service_url = os.getenv(
        "SADTALKER_SERVICE_URL",
        "http://127.0.0.1:8001",
    ).rstrip("/")

    source_image = validate_file(
        image_path,
        "Source avatar image",
    )

    source_audio = validate_file(
        audio_path,
        "Input audio",
    )

    print()
    print("========================================")
    print("Connecting to Aloko SadTalker Service")
    print("========================================")
    print(f"Service: {service_url}")
    print()

    boundary = uuid.uuid4().hex.encode()

    def add_file(field_name: str, path: Path):
        filename = path.name
        content = path.read_bytes()

        parts = []
        parts.append(
            b"--" + boundary + b"\r\n"
        )
        parts.append(
            (
                f'Content-Disposition: form-data; '
                f'name="{field_name}"; filename="{filename}"\r\n'
            ).encode()
        )
        parts.append(
            b"Content-Type: application/octet-stream\r\n\r\n"
        )
        parts.append(content)
        parts.append(b"\r\n")

        return b"".join(parts)

    body = b"".join(
        [
            add_file("avatar", source_image),
            add_file("audio", source_audio),
            b"--" + boundary + b"--\r\n",
        ]
    )

    request = urllib.request.Request(
        f"{service_url}/generate",
        data=body,
        method="POST",
        headers={
            "Content-Type": (
                f"multipart/form-data; boundary={boundary.decode()}"
            ),
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )
    except Exception as exc:
        raise RuntimeError(
            "Could not connect to SadTalker service: "
            f"{exc}"
        ) from exc

    job_id = payload.get("job_id")

    if not job_id:
        raise RuntimeError(
            f"SadTalker service returned an invalid response: {payload}"
        )

    print(f"SadTalker job: {job_id}")
    print()

    # Poll the dedicated SadTalker service.
    while True:

        try:
            with urllib.request.urlopen(
                f"{service_url}/jobs/{job_id}",
                timeout=30,
            ) as response:
                status = json.loads(
                    response.read().decode("utf-8")
                )
        except Exception as exc:
            raise RuntimeError(
                "Lost connection to SadTalker service: "
                f"{exc}"
            ) from exc

        progress = status.get("progress", 0)
        stage = status.get("stage", "Processing")
        job_status = status.get("status")

        print(
            f"SadTalker {progress}% - {stage}",
            flush=True,
        )

        if job_status == "completed":

            video_url = status.get("video")

            if not video_url:
                raise RuntimeError(
                    "SadTalker completed but returned no video URL."
                )

            if video_url.startswith("/"):
                video_url = service_url + video_url

            final_filename = f"{uuid.uuid4()}.mp4"
            final_path = (
                VIDEO_STORAGE_DIR / final_filename
            )

            try:
                urllib.request.urlretrieve(
                    video_url,
                    str(final_path),
                )
            except Exception as exc:
                raise RuntimeError(
                    "SadTalker completed, but Aloko could not "
                    f"download the generated MP4: {exc}"
                ) from exc

            if not final_path.exists():
                raise RuntimeError(
                    "Generated MP4 was not saved to Aloko storage."
                )

            if final_path.stat().st_size == 0:
                raise RuntimeError(
                    "Generated MP4 is empty."
                )

            print()
            print("========================================")
            print("SadTalker video created successfully")
            print("========================================")
            print(f"Aloko video: {final_path}")
            print()

            return str(final_path)

        if job_status == "failed":

            error = status.get(
                "error",
                "Unknown SadTalker error",
            )

            raise RuntimeError(
                f"SadTalker generation failed: {error}"
            )

        time.sleep(3)

