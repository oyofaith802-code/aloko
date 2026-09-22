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
# APPLY SCENE CAMERA / CAPTIONS
# ============================================================

def apply_scene_effects(
    video_path: str,
    *,
    camera: str | None = None,
    captions_enabled: bool = True,
    caption_text: str | None = None,
) -> str:
    """
    Apply safe post-processing to an individual Creator scene.

    Camera controls are implemented with FFmpeg crop/scale filters.
    Captions are burned into the scene when enabled.
    """

    source = Path(video_path).resolve()

    if not source.exists():
        raise FileNotFoundError(
            f"Scene video not found: {source}"
        )

    if not source.is_file():
        raise FileNotFoundError(
            f"Scene video is not a file: {source}"
        )

    render_id = str(uuid.uuid4())
    render_dir = CREATOR_RENDER_DIR / render_id
    render_dir.mkdir(parents=True, exist_ok=True)

    output = render_dir / "processed_scene.mp4"

    filters = []

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    camera_value = (camera or "Default").strip().lower()

    if camera_value == "close-up":
        filters.append(
            "crop=iw*0.82:ih*0.82:"
            "(iw-iw*0.82)/2:(ih-ih*0.82)/2,"
            "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        )

    elif camera_value == "medium":
        filters.append(
            "crop=iw*0.92:ih*0.92:"
            "(iw-iw*0.92)/2:(ih-ih*0.92)/2,"
            "scale=trunc(iw/0.92/2)*2:trunc(ih/0.92/2)*2"
        )

    elif camera_value == "wide":
        filters.append(
            "scale=trunc(iw*0.92/2)*2:"
            "trunc(ih*0.92/2)*2,"
            "pad=iw/0.92:ih/0.92:"
            "(ow-iw)/2:(oh-ih)/2"
        )

    # --------------------------------------------------------
    # CAPTIONS
    # --------------------------------------------------------

    if captions_enabled and caption_text:
        safe_text = (
            caption_text
            .replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\'")
            .replace("\n", " ")
            .replace("\r", " ")
        )

        # Keep captions readable and safely inside the frame.
        filters.append(
            "drawtext="
            "fontcolor=white:"
            "fontsize=28:"
            "borderw=3:"
            "bordercolor=black:"
            "x=(w-text_w)/2:"
            "y=h-text_h-40:"
            f"text='{safe_text}'"
        )

    if not filters:
        return str(source)

    command = [
        FFMPEG_PATH,
        "-y",
        "-i",
        str(source),
        "-vf",
        ",".join(filters),
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
        str(output),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg scene processing failed.\n\n"
            f"{result.stderr[-5000:]}"
        )

    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError(
            "FFmpeg scene processing finished "
            "without creating a valid video."
        )

    return str(output)



# ============================================================
# VIDEO DURATION
# ============================================================

def get_video_duration(
    video_path: str,
) -> float:
    """
    Read the duration of an MP4 using FFprobe.
    """

    ffprobe_path = str(
        Path(FFMPEG_PATH).with_name("ffprobe.exe")
    )

    if not os.path.exists(ffprobe_path):
        raise FileNotFoundError(
            f"FFprobe not found: {ffprobe_path}"
        )

    command = [
        ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFprobe failed to read video duration.\n\n"
            f"{result.stderr[-5000:]}"
        )

    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid video duration returned for: {video_path}"
        ) from exc

    if duration <= 0:
        raise RuntimeError(
            f"Video duration is invalid: {video_path}"
        )

    return duration


# ============================================================
# TRANSITION-AWARE VIDEO COMBINATION
# ============================================================

def combine_videos(
    video_paths: list[str],
    transitions: list[str] | None = None,
) -> str:
    """
    Combine Creator scene videos.

    Supported transitions:

    - Cut
    - Fade
    - Crossfade

    Cut uses the existing fast concatenation path.

    Fade uses a fade-through-black visual transition.

    Crossfade uses a visual dissolve between adjacent scenes.

    Audio is preserved for all transition types.
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

    # --------------------------------------------------------
    # NORMALIZE TRANSITIONS
    # --------------------------------------------------------

    transition_values = []

    for index in range(len(validated_paths) - 1):

        value = (
            transitions[index]
            if transitions and index < len(transitions)
            else "Cut"
        )

        value = str(value or "Cut").strip().lower()

        if value not in {
            "cut",
            "fade",
            "crossfade",
        }:
            value = "Cut"

        transition_values.append(value)

    # --------------------------------------------------------
    # FAST PATH: ALL CUT
    # --------------------------------------------------------

    if all(
        value == "cut"
        for value in transition_values
    ):
        return _combine_videos_cut(
            validated_paths
        )

    # --------------------------------------------------------
    # TRANSITION PATH
    # --------------------------------------------------------

    render_id = str(uuid.uuid4())

    render_dir = (
        CREATOR_RENDER_DIR / render_id
    )

    render_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_filename = (
        f"{uuid.uuid4()}.mp4"
    )

    final_path = (
        VIDEO_STORAGE_DIR /
        final_filename
    )

    durations = [
        get_video_duration(path)
        for path in validated_paths
    ]

    # --------------------------------------------------------
    # TRANSITION DURATIONS
    # --------------------------------------------------------

    transition_durations = []

    for index, transition in enumerate(
        transition_values
    ):

        if transition == "crossfade":
            requested = 0.8

        elif transition == "fade":
            requested = 0.5

        else:
            # A tiny duration gives a near-instant cut
            # when mixed with other transition types.
            requested = 0.001

        max_duration = min(
            durations[index],
            durations[index + 1],
        )

        transition_durations.append(
            min(
                requested,
                max_duration / 3,
            )
        )

    # --------------------------------------------------------
    # BUILD FILTER GRAPH
    # --------------------------------------------------------

    filter_parts = []

    # Normalize every video stream so xfade receives
    # consistent timestamps, frame rate and pixel format.
    for index in range(
        len(validated_paths)
    ):

        filter_parts.append(
            f"[{index}:v:0]"
            f"settb=AVTB,"
            f"fps=30,"
            f"format=yuv420p"
            f"[v{index}]"
        )

    # Normalize every audio stream.
    #
    # SadTalker scenes should contain audio because the
    # scene was generated from the selected voice.
    for index in range(
        len(validated_paths)
    ):

        filter_parts.append(
            f"[{index}:a:0]"
            f"aresample=async=1,"
            f"asetpts=PTS-STARTPTS"
            f"[a{index}]"
        )

    # --------------------------------------------------------
    # VIDEO XFADE CHAIN
    # --------------------------------------------------------

    current_video = "v0"

    current_video_duration = durations[0]

    for index, transition in enumerate(
        transition_values
    ):

        duration = transition_durations[index]

        next_video = f"v{index + 1}"

        output_video = f"xv{index}"

        offset = max(
            0.0,
            current_video_duration - duration,
        )

        # ----------------------------------------------------
        # VISUAL TRANSITION
        # ----------------------------------------------------

        if transition == "fade":

            # Fade through black.
            transition_name = "fadeblack"

        elif transition == "crossfade":

            # Dissolve/visual crossfade.
            transition_name = "fade"

        else:

            # Near-instant boundary for a mixed
            # Cut/Fade/Crossfade project.
            transition_name = "fade"

        filter_parts.append(
            f"[{current_video}]"
            f"[{next_video}]"
            f"xfade="
            f"transition={transition_name}:"
            f"duration={duration:.3f}:"
            f"offset={offset:.3f}"
            f"[{output_video}]"
        )

        current_video = output_video

        current_video_duration = (
            current_video_duration
            + durations[index + 1]
            - duration
        )

    # --------------------------------------------------------
    # AUDIO ACROSSFADE CHAIN
    # --------------------------------------------------------

    current_audio = "a0"

    for index, transition in enumerate(
        transition_values
    ):

        duration = transition_durations[index]

        next_audio = f"a{index + 1}"

        output_audio = f"xa{index}"

        filter_parts.append(
            f"[{current_audio}]"
            f"[{next_audio}]"
            f"acrossfade="
            f"d={duration:.3f}:"
            f"c1=tri:"
            f"c2=tri"
            f"[{output_audio}]"
        )

        current_audio = output_audio

    filter_complex = ";".join(
        filter_parts
    )

    # --------------------------------------------------------
    # FFmpeg COMMAND
    # --------------------------------------------------------

    command = [
        FFMPEG_PATH,
        "-y",
    ]

    for video_path in validated_paths:
        command.extend([
            "-i",
            video_path,
        ])

    command.extend([
        "-filter_complex",
        filter_complex,

        # Final video.
        "-map",
        f"[{current_video}]",

        # Final audio.
        "-map",
        f"[{current_audio}]",

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
    print(
        f"Transitions: {transition_values}"
    )

    print(
        f"Transition durations: "
        f"{[round(value, 3) for value in transition_durations]}"
    )

    print()
    print(
        "Audio preservation: ENABLED"
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg failed to combine "
            "Creator scenes with transitions.\n\n"
            f"{result.stderr[-8000:]}"
        )

    if (
        not final_path.exists()
        or final_path.stat().st_size == 0
    ):

        raise RuntimeError(
            "FFmpeg completed but the "
            "transition video was not created."
        )

    print()
    print("========================================")
    print("Creator final video created")
    print("========================================")
    print(final_path)
    print()

    return str(final_path)


# ============================================================
# ORIGINAL CUT CONCATENATION
# ============================================================

def _combine_videos_cut(
    validated_paths: list[str],
) -> str:
    """
    Original fast concatenation path used when
    no transition is requested.
    """

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

        fallback_command = [
            FFMPEG_PATH,
            "-y",
        ]

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

