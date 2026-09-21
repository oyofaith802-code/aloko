# app/services/sadtalker_service.py

import shutil
import subprocess
import uuid
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(
    r"C:\Users\USER\Desktop\aloko\backend"
)

SADTALKER_DIR = Path(
    r"C:\Users\USER\Desktop\aloko\SadTalker"
)

SADTALKER_PYTHON = Path(
    r"C:\Users\USER\anaconda3\envs\sadtalker\python.exe"
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
    r"C:\Users\USER\AppData\Local\Microsoft\WinGet"
    r"\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build-shared\bin\ffmpeg.exe"
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

    print()
    print("========================================")
    print("Starting SadTalker")
    print("========================================")
    print()

    # --------------------------------------------------------
    # Validate dependencies
    # --------------------------------------------------------

    validate_dependencies()

    # --------------------------------------------------------
    # Validate image
    # --------------------------------------------------------

    source_image = validate_file(
        image_path,
        "Source avatar image",
    )

    # --------------------------------------------------------
    # Convert audio
    # --------------------------------------------------------

    driven_audio = convert_audio_to_wav(
        audio_path
    )

    driven_audio_path = validate_file(
        driven_audio,
        "SadTalker audio",
    )

    # --------------------------------------------------------
    # Remember existing output files
    # --------------------------------------------------------

    existing_files = set(
        RESULTS_DIR.glob("*.mp4")
    )

    # --------------------------------------------------------
    # SadTalker command
    # --------------------------------------------------------

    command = [
        str(SADTALKER_PYTHON),

        str(INFERENCE_SCRIPT),

        "--driven_audio",
        str(driven_audio_path),

        "--source_image",
        str(source_image),

        "--result_dir",
        str(RESULTS_DIR),

        "--still",

        "--preprocess",
        "full",

        "--cpu",
    ]

    print("SadTalker command:")
    print()

    print(
        " ".join(
            f'"{part}"'
            if " " in part
            else part
            for part in command
        )
    )

    print()
    print("========================================")
    print("Running SadTalker...")
    print("========================================")
    print()

    # --------------------------------------------------------
    # RUN SADTALKER
    #
    # IMPORTANT:
    # We intentionally capture stdout/stderr so that
    # the real SadTalker error is returned instead of
    # only showing "exit status 1".
    # --------------------------------------------------------

    result = subprocess.run(
        command,
        cwd=str(SADTALKER_DIR),
        capture_output=True,
        text=True,
    )

    # --------------------------------------------------------
    # PRINT FULL OUTPUT
    # --------------------------------------------------------

    print()
    print("========================================")
    print("SADTALKER STDOUT")
    print("========================================")

    if result.stdout:
        print(result.stdout)
    else:
        print("(no stdout)")

    print()
    print("========================================")
    print("SADTALKER STDERR")
    print("========================================")

    if result.stderr:
        print(result.stderr)
    else:
        print("(no stderr)")

    print()
    print("========================================")
    print(
        f"SadTalker return code: {result.returncode}"
    )
    print("========================================")
    print()

    # --------------------------------------------------------
    # Handle SadTalker failure
    # --------------------------------------------------------

    if result.returncode != 0:

        stdout_tail = (
            result.stdout[-8000:]
            if result.stdout
            else "(no stdout)"
        )

        stderr_tail = (
            result.stderr[-8000:]
            if result.stderr
            else "(no stderr)"
        )

        raise RuntimeError(
            "SadTalker failed.\n\n"

            "================ STDOUT ================\n"
            f"{stdout_tail}\n\n"

            "================ STDERR ================\n"
            f"{stderr_tail}"
        )

    # --------------------------------------------------------
    # Find generated video
    # --------------------------------------------------------

    generated_video = (
        find_new_sadtalker_video(
            existing_files
        )
    )

    if generated_video is None:

        # Sometimes SadTalker may overwrite/reuse a result.
        # In that case, look for the newest MP4.

        all_mp4_files = list(
            RESULTS_DIR.glob("*.mp4")
        )

        if all_mp4_files:

            all_mp4_files.sort(
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )

            generated_video = (
                all_mp4_files[0]
            )

    # --------------------------------------------------------
    # Make sure output exists
    # --------------------------------------------------------

    if generated_video is None:

        raise RuntimeError(
            "SadTalker completed successfully, "
            "but no MP4 video was found in:\n"
            f"{RESULTS_DIR}"
        )

    if not generated_video.exists():

        raise RuntimeError(
            "SadTalker output video does not exist:\n"
            f"{generated_video}"
        )

    if generated_video.stat().st_size == 0:

        raise RuntimeError(
            "SadTalker created an empty video:\n"
            f"{generated_video}"
        )

    # --------------------------------------------------------
    # Copy final video into Aloko storage
    # --------------------------------------------------------

    final_filename = (
        f"{uuid.uuid4()}.mp4"
    )

    final_path = (
        VIDEO_STORAGE_DIR
        / final_filename
    )

    try:

        shutil.copy2(
            generated_video,
            final_path,
        )

    except OSError as exc:

        raise RuntimeError(
            "Failed to copy SadTalker video "
            "into Aloko storage."
        ) from exc

    # --------------------------------------------------------
    # Validate copied video
    # --------------------------------------------------------

    if not final_path.exists():

        raise RuntimeError(
            "Final Aloko video was not created."
        )

    if final_path.stat().st_size == 0:

        raise RuntimeError(
            "Final Aloko video is empty."
        )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print()
    print("========================================")
    print("SadTalker video created successfully")
    print("========================================")
    print()
    print(
        f"SadTalker output: {generated_video}"
    )
    print(
        f"Aloko video:      {final_path}"
    )
    print()

    return str(final_path)