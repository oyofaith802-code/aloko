import os
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

STORAGE_DIR = BACKEND_DIR / "storage"

VIDEO_STORAGE_DIR = (
    STORAGE_DIR / "videos"
)

CREATOR_RENDER_DIR = (
    STORAGE_DIR / "creator_renders"
)

FFMPEG_PATH = (
    r"C:\Users\USER\AppData\Local\Microsoft\WinGet"
    r"\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build-shared\bin\ffmpeg.exe"
)


# ============================================================
# DIRECTORIES
# ============================================================

VIDEO_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CREATOR_RENDER_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# VALIDATE VIDEO
# ============================================================

def validate_video_file(
    video_path: str,
) -> str:

    path = Path(video_path).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Video file not found: {path}"
        )

    if path.suffix.lower() != ".mp4":
        raise ValueError(
            f"Expected MP4 video: {path}"
        )

    return str(path)


# ============================================================
# CONCATENATE VIDEOS
# ============================================================

def combine_videos(
    video_paths: list[str],
) -> str:
    """
    Combine multiple scene MP4 files into one final MP4.

    First tries stream-copy concatenation.

    If the source videos are not compatible,
    automatically falls back to FFmpeg re-encoding.
    """

    if not video_paths:
        raise ValueError(
            "No scene videos were provided."
        )

    if not os.path.exists(FFMPEG_PATH):
        raise FileNotFoundError(
            f"FFmpeg not found: {FFMPEG_PATH}"
        )

    validated_paths = [
        validate_video_file(path)
        for path in video_paths
    ]

    render_id = str(
        uuid.uuid4()
    )

    render_dir = (
        CREATOR_RENDER_DIR / render_id
    )

    render_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    concat_file = (
        render_dir / "concat.txt"
    )

    final_filename = (
        f"{uuid.uuid4()}.mp4"
    )

    final_path = (
        VIDEO_STORAGE_DIR /
        final_filename
    )

    # ========================================================
    # CREATE CONCAT FILE
    # ========================================================

    with open(
        concat_file,
        "w",
        encoding="utf-8",
    ) as file:

        for video_path in validated_paths:

            safe_path = (
                video_path
                .replace("\\", "/")
                .replace("'", "'\\''")
            )

            file.write(
                f"file '{safe_path}'\n"
            )

    # ========================================================
    # FIRST METHOD
    # STREAM COPY
    # ========================================================

    copy_command = [
        FFMPEG_PATH,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(final_path),
    ]

    print()
    print("========================================")
    print("Combining Creator scene videos")
    print("========================================")

    for index, path in enumerate(
        validated_paths,
        start=1,
    ):
        print(
            f"Scene {index}: {path}"
        )

    print()
    print("Trying stream-copy concatenation...")

    copy_result = subprocess.run(
        copy_command,
        capture_output=True,
        text=True,
    )

    if (
        copy_result.returncode != 0
        or not final_path.exists()
        or final_path.stat().st_size == 0
    ):

        print(
            "Stream-copy failed."
        )

        if final_path.exists():
            final_path.unlink()

        # ====================================================
        # FALLBACK
        # RE-ENCODE
        # ====================================================

        print(
            "Trying FFmpeg re-encoding..."
        )

        filter_inputs = []

        for index in range(
            len(validated_paths)
        ):
            filter_inputs.append(
                f"[{index}:v:0]"
                f"[{index}:a:0]"
            )

        filter_complex = (
            "".join(filter_inputs)
            + f"concat=n={len(validated_paths)}"
              ":v=1:a=1[outv][outa]"
        )

        fallback_command = []

        fallback_command.extend([
            FFMPEG_PATH,
            "-y",
        ])

        for video_path in validated_paths:
            fallback_command.extend([
                "-i",
                video_path,
            ])

        fallback_command.extend([
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(final_path),
        ])

        result = subprocess.run(
            fallback_command,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FFmpeg failed to combine "
                "the Creator scene videos.\n\n"
                f"{result.stderr[-5000:]}"
            )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    if not final_path.exists():
        raise RuntimeError(
            "FFmpeg finished but final video "
            "was not created."
        )

    if final_path.stat().st_size == 0:
        raise RuntimeError(
            "Final video was created but is empty."
        )

    print()
    print("========================================")
    print("Creator final video created")
    print("========================================")
    print(final_path)
    print()

    return str(final_path)