# app/routes/creator_render.py

import os
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user

from app.models.user import User
from app.models.creator_project import CreatorProject
from app.models.creator_scene import CreatorScene
from app.models.avatar import Avatar
from app.models.voice import Voice

from app.services.tts_service import generate_speech
from app.services.sadtalker_service import (
    generate_sadtalker_video,
)
from app.services.voice_catalog import get_all_voices
from app.services.personal_voice_service import (
    generate_personal_voice_speech,
    PersonalVoiceError,
)
from app.services.video_compositor import (
    combine_videos,
    apply_scene_effects,
)


router = APIRouter(
    prefix="/projects",
    tags=["Creator Rendering"],
)


# ============================================================
# STORAGE
# ============================================================

STORAGE_DIR = Path("storage")


# ============================================================
# AVATAR PATH
# ============================================================

def get_avatar_file_path(
    image_url: str,
) -> str:
    if not image_url:
        raise HTTPException(
            status_code=404,
            detail="Avatar image path is missing.",
        )

    normalized = image_url.replace(
        "\\",
        "/",
    )

    # Handle full URLs such as:
    # https://aloko.onrender.com/storage/avatars/example.jpg
    if normalized.startswith(("http://", "https://")):
        filename = Path(
            normalized.split("?", 1)[0]
        ).name

        if not filename:
            raise HTTPException(
                status_code=404,
                detail="Avatar image filename is missing.",
            )

        cache_dir = STORAGE_DIR / "avatars" / "remote_cache"
        cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        cached_path = cache_dir / filename

        if cached_path.exists():
            return str(cached_path.resolve())

        try:
            request = Request(
                normalized,
                headers={
                    "User-Agent": "Aloko-Creator/1.0",
                },
            )

            with urlopen(
                request,
                timeout=30,
            ) as response:
                data = response.read()

            if not data:
                raise RuntimeError(
                    "Downloaded avatar file is empty."
                )

            cached_path.write_bytes(data)

            return str(cached_path.resolve())

        except Exception as exc:
            raise HTTPException(
                status_code=404,
                detail="Avatar image could not be downloaded.",
            ) from exc

    storage_marker = "/storage/"

    if storage_marker in normalized:
        relative_path = normalized.split(
            storage_marker,
            1,
        )[1]

        file_path = (
            STORAGE_DIR /
            Path(relative_path)
        )
    else:
        file_path = Path(normalized)

    return str(file_path.resolve())


# ============================================================
# OWNED PROJECT
# ============================================================

def get_owned_project(
    project_id: int,
    current_user: User,
    db: Session,
):

    project = (
        db.query(CreatorProject)
        .filter(
            CreatorProject.id == project_id,
            CreatorProject.user_id
            == current_user.id,
        )
        .first()
    )

    if not project:

        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return project


# ============================================================
# BUILT-IN VOICE
# ============================================================

async def get_builtin_voice(
    requested_voice: str | None,
):

    voices = await get_all_voices()

    # --------------------------------------------------------
    # Requested voice
    # --------------------------------------------------------

    if requested_voice:

        requested_voice = (
            requested_voice.strip()
        )

        selected = next(
            (
                voice
                for voice in voices
                if voice.get("tts_voice")
                == requested_voice
            ),
            None,
        )

        if not selected:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid built-in voice selected."
                ),
            )

        return selected

    # --------------------------------------------------------
    # Default built-in voice
    # --------------------------------------------------------

    default_voice = next(
        (
            voice
            for voice in voices
            if voice.get("tts_voice")
            == "en-US-AriaNeural"
        ),
        None,
    )

    if default_voice:

        return default_voice

    # --------------------------------------------------------
    # Safe fallback
    # --------------------------------------------------------

    return {
        "tts_voice": "en-US-AriaNeural",
        "name": "Aria",
        "language": "en",
        "language_code": "en-US",
        "country": "US",
        "accent": "en-US",
        "gender": "female",
    }


# ============================================================
# RENDER CREATOR PROJECT
# ============================================================

@router.post(
    "/{project_id}/render"
)
async def render_creator_project(
    project_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    ),
):

    # ========================================================
    # PROJECT OWNERSHIP
    # ========================================================

    project = get_owned_project(
        project_id,
        current_user,
        db,
    )

    # ========================================================
    # GET SCENES
    # ========================================================

    scenes = (
        db.query(CreatorScene)
        .filter(
            CreatorScene.project_id
            == project.id
        )
        .order_by(
            CreatorScene.scene_order.asc()
        )
        .all()
    )

    if not scenes:

        raise HTTPException(
            status_code=400,
            detail=(
                "Project has no scenes. "
                "Add at least one scene before rendering."
            ),
        )

    # ========================================================
    # UPDATE PROJECT STATUS
    # ========================================================

    project.render_status = "rendering"
    project.render_error = None
    project.final_video_url = None

    db.commit()

    scene_video_paths = []
    scene_transitions = []
    scene_results = []

    try:

        # ====================================================
        # PROCESS EACH SCENE
        # ====================================================

        for scene in scenes:

            print()
            print(
                "========================================"
            )
            print(
                f"Rendering Scene {scene.scene_order}"
            )
            print(
                "========================================"
            )

            # =================================================
            # SCRIPT
            # =================================================

            script = (
                (scene.script or "")
                .strip()
            )

            if not script:

                raise RuntimeError(
                    f"Scene {scene.scene_order} "
                    "does not contain a script."
                )

            if len(script) > 5000:

                raise RuntimeError(
                    f"Scene {scene.scene_order} "
                    "script is longer than 5000 characters."
                )

            # =================================================
            # AVATAR
            # =================================================

            if scene.avatar_id is None:

                raise RuntimeError(
                    f"Scene {scene.scene_order} "
                    "does not have an avatar selected."
                )

            avatar = (
                db.query(Avatar)
                .filter(
                    Avatar.id
                    == scene.avatar_id,
                    Avatar.user_id
                    == current_user.id,
                )
                .first()
            )

            if not avatar:

                raise RuntimeError(
                    f"Avatar for Scene "
                    f"{scene.scene_order} "
                    "was not found."
                )

            avatar_path = (
                get_avatar_file_path(
                    avatar.image_url
                )
            )

            if not os.path.exists(
                avatar_path
            ):

                raise RuntimeError(
                    f"Avatar file for Scene "
                    f"{scene.scene_order} "
                    "was not found."
                )

            # =================================================
            # VOICE
            # =================================================

            selected_voice = None
            custom_voice = None

            # -------------------------------------------------
            # PERSONAL VOICE HAS PRIORITY WHEN voice_id EXISTS
            # -------------------------------------------------

            if scene.voice_id is not None:

                custom_voice = (
                    db.query(Voice)
                    .filter(
                        Voice.id
                        == scene.voice_id,
                        Voice.user_id
                        == current_user.id,
                    )
                    .first()
                )

                if not custom_voice:

                    raise RuntimeError(
                        f"Voice for Scene "
                        f"{scene.scene_order} "
                        "was not found."
                    )

                if (
                    custom_voice.voice_type
                    != "custom"
                ):

                    raise RuntimeError(
                        f"Voice for Scene "
                        f"{scene.scene_order} "
                        "is not a personal voice."
                    )

                print(
                    f"Using personal voice "
                    f"'{custom_voice.name}' "
                    f"for Scene {scene.scene_order}."
                )

            else:

                # -------------------------------------------------
                # BUILT-IN VOICE
                #
                # IMPORTANT:
                # Use the voice saved on this specific scene.
                # If none exists, get_builtin_voice() falls back
                # to Aria.
                # -------------------------------------------------

                selected_voice = (
                    await get_builtin_voice(
                        scene.voice
                    )
                )

                print(
                    f"Using built-in voice "
                    f"'{selected_voice['name']}' "
                    f"for Scene {scene.scene_order}."
                )

            # =================================================
            # GENERATE AUDIO
            # =================================================

            print(
                f"Generating audio for "
                f"Scene {scene.scene_order}..."
            )

            # -------------------------------------------------
            # PERSONAL VOICE
            # -------------------------------------------------

            if custom_voice is not None:

                try:

                    audio_bytes = (
                        generate_personal_voice_speech(
                            text=script,
                            voice=custom_voice,
                        )
                    )

                except PersonalVoiceError as exc:

                    raise RuntimeError(
                        f"Personal voice generation "
                        f"failed for Scene "
                        f"{scene.scene_order}: "
                        f"{str(exc)}"
                    ) from exc

                if not audio_bytes:

                    raise RuntimeError(
                        f"Personal voice engine "
                        f"returned no audio for "
                        f"Scene {scene.scene_order}."
                    )

                # ------------------------------------------------
                # SAVE PERSONAL VOICE AUDIO
                # ------------------------------------------------

                voice_audio_dir = (
                    STORAGE_DIR / "audio"
                )

                voice_audio_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                audio_filename = (
                    f"{custom_voice.id}_"
                    f"{scene.id}_"
                    f"{uuid.uuid4().hex}.mp3"
                )

                audio_path = (
                    voice_audio_dir
                    / audio_filename
                )

                with open(
                    audio_path,
                    "wb",
                ) as audio_file:

                    audio_file.write(
                        audio_bytes
                    )

                audio_path = str(
                    audio_path.resolve()
                )

            # -------------------------------------------------
            # BUILT-IN EDGE TTS
            # -------------------------------------------------

            else:

                audio_path = await generate_speech(
                    text=script,
                    voice=selected_voice[
                        "tts_voice"
                    ],
                )

                if not audio_path:

                    raise RuntimeError(
                        f"Speech service returned "
                        f"no audio for Scene "
                        f"{scene.scene_order}."
                    )

                audio_path = os.path.abspath(
                    audio_path
                )

            # =================================================
            # VERIFY AUDIO
            # =================================================

            if not os.path.exists(
                audio_path
            ):

                raise RuntimeError(
                    f"Generated audio file for "
                    f"Scene {scene.scene_order} "
                    "was not found."
                )

            # =================================================
            # SADTALKER
            # =================================================

            print(
                f"Generating SadTalker video "
                f"for Scene {scene.scene_order}..."
            )

            scene_video = (
                generate_sadtalker_video(
                    image_path=avatar_path,
                    audio_path=audio_path,
                )
            )

            if not scene_video:

                raise RuntimeError(
                    f"SadTalker returned no video "
                    f"for Scene "
                    f"{scene.scene_order}."
                )

            scene_video = os.path.abspath(
                scene_video
            )

            if not os.path.exists(
                scene_video
            ):

                raise RuntimeError(
                    f"Scene video file for "
                    f"Scene {scene.scene_order} "
                    "was not found."
                )

            # =================================================
            # APPLY SCENE EFFECTS
            # =================================================

            print(
                f"Applying scene settings "
                f"for Scene {scene.scene_order}..."
            )

            processed_scene_video = apply_scene_effects(
                scene_video,
                camera=scene.camera,
                captions_enabled=bool(
                    scene.captions_enabled
                ),
                caption_text=script,
            )

            if not processed_scene_video:
                raise RuntimeError(
                    f"Scene effects processor returned "
                    f"no video for Scene "
                    f"{scene.scene_order}."
                )

            processed_scene_video = os.path.abspath(
                processed_scene_video
            )

            if not os.path.exists(
                processed_scene_video
            ):
                raise RuntimeError(
                    f"Processed scene video for "
                    f"Scene {scene.scene_order} "
                    "was not found."
                )

            scene_video_paths.append(
                processed_scene_video
            )

            # Transition applies between this scene
            # and the following scene.
            scene_transitions.append(
                scene.transition or "Cut"
            )

            # =================================================
            # SCENE RESULT
            # =================================================

            if custom_voice is not None:

                voice_name = (
                    custom_voice.name
                )

                voice_type = "personal"

            else:

                voice_name = (
                    selected_voice.get(
                        "name"
                    )
                    or selected_voice.get(
                        "tts_voice"
                    )
                )

                voice_type = "built_in"

            scene_results.append(
                {
                    "scene_id": scene.id,
                    "scene_order": scene.scene_order,
                    "status": "completed",
                    "video_file": scene_video,
                    "avatar_id": avatar.id,
                    "voice": voice_name,
                    "voice_type": voice_type,
                }
            )

        # ====================================================
        # COMBINE SCENES
        # ====================================================

        print()
        print(
            "========================================"
        )
        print(
            "Combining all Creator scenes..."
        )
        print(
            "========================================"
        )

        final_path = combine_videos(
            scene_video_paths,
            transitions=scene_transitions[:-1],
        )

        final_path = os.path.abspath(
            final_path
        )

        if not os.path.exists(
            final_path
        ):

            raise RuntimeError(
                "Final Creator video was not found."
            )

        filename = os.path.basename(
            final_path
        )

        final_video_url = (
            f"/storage/videos/{filename}"
        )

        # ====================================================
        # SAVE PROJECT
        # ====================================================

        project.render_status = (
            "completed"
        )

        project.status = (
            "completed"
        )

        project.final_video_url = (
            final_video_url
        )

        project.render_error = None

        db.commit()
        db.refresh(project)

        # ====================================================
        # RESPONSE
        # ====================================================

        return {
            "message": (
                "Creator project rendered successfully."
            ),
            "project_id": project.id,
            "project_name": project.name,
            "status": project.status,
            "render_status": (
                project.render_status
            ),
            "video_url": final_video_url,
            "scene_count": len(
                scene_results
            ),
            "scenes": [
                {
                    "scene_id": item[
                        "scene_id"
                    ],
                    "scene_order": item[
                        "scene_order"
                    ],
                    "status": item[
                        "status"
                    ],
                    "avatar_id": item[
                        "avatar_id"
                    ],
                    "voice": item[
                        "voice"
                    ],
                    "voice_type": item[
                        "voice_type"
                    ],
                }
                for item in scene_results
            ],
        }

    # ========================================================
    # HTTP ERROR
    # ========================================================

    except HTTPException as exc:

        project.render_status = (
            "failed"
        )

        project.render_error = (
            str(exc.detail)
        )

        db.commit()

        raise

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as exc:

        project.render_status = (
            "failed"
        )

        project.render_error = (
            str(exc)
        )

        db.commit()

        print()
        print(
            "========================================"
        )
        print(
            "CREATOR RENDER FAILED"
        )
        print(
            "========================================"
        )
        print(
            str(exc)
        )
        print()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Creator rendering failed: "
                f"{str(exc)}"
            ),
        ) from exc