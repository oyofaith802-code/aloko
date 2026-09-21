import json
import os
import re
from typing import Any

import ollama
from sqlalchemy.orm import Session

from app.models.avatar import Avatar
from app.models.voice import Voice


OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:latest",
)

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434",
)

client = ollama.Client(
    host=OLLAMA_HOST
)


class AIDirectorError(Exception):
    """Raised when the AI Director cannot create a valid plan."""


PLACEHOLDER_VALUES = {
    "professional project name",
    "short project description",
    "narration for this scene",
    "narration for the first scene",
    "specific presenter action",
    "specific environment",
    "camera direction",
    "transition to next scene",
    "music suggestion",
}


def _extract_json(
    text: str,
) -> dict[str, Any]:

    if not text:
        raise AIDirectorError(
            "AI Director returned an empty response."
        )

    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if (
        start == -1
        or end == -1
        or end <= start
    ):
        raise AIDirectorError(
            "AI Director returned invalid JSON."
        )

    candidate = cleaned[
        start : end + 1
    ]

    try:
        result = json.loads(candidate)

    except json.JSONDecodeError as exc:
        raise AIDirectorError(
            "AI Director returned malformed JSON."
        ) from exc

    if not isinstance(result, dict):
        raise AIDirectorError(
            "AI Director response must be a JSON object."
        )

    return result


def _clean_text(
    value: Any,
    default: str = "",
) -> str:

    if value is None:
        return default

    return str(value).strip()


def _safe_int(
    value: Any,
) -> int | None:

    if value is None or value == "":
        return None

    try:
        return int(value)

    except (
        TypeError,
        ValueError,
    ):
        return None


def _is_placeholder(
    value: Any,
) -> bool:

    text = _clean_text(
        value
    ).lower()

    return (
        text in PLACEHOLDER_VALUES
        or text.startswith("specific ")
    )


def _normalize_scene(
    scene: Any,
) -> dict[str, Any]:

    if not isinstance(
        scene,
        dict,
    ):
        scene = {}

    return {
        "script": _clean_text(
            scene.get("script")
        ),

        "avatar_id": _safe_int(
            scene.get("avatar_id")
        ),

        "voice_id": _safe_int(
            scene.get("voice_id")
        ),

        "voice": _clean_text(
            scene.get("voice")
        ),

        "action": _clean_text(
            scene.get("action")
        ),

        "environment": _clean_text(
            scene.get("environment")
        ),

        "camera": _clean_text(
            scene.get("camera")
        ),

        "transition": _clean_text(
            scene.get("transition")
        ),

        "captions_enabled": bool(
            scene.get(
                "captions_enabled",
                True,
            )
        ),

        "background_music": _clean_text(
            scene.get("background_music")
        ),
    }


def _validate_plan_content(
    plan: dict[str, Any],
) -> None:

    project = plan.get(
        "project"
    )

    scenes = plan.get(
        "scenes"
    )

    if not isinstance(
        project,
        dict,
    ):
        raise AIDirectorError(
            "AI Director did not return a valid project."
        )

    if _is_placeholder(
        project.get("name")
    ):
        raise AIDirectorError(
            "AI Director returned a placeholder project name."
        )

    if (
        not isinstance(
            scenes,
            list,
        )
        or not scenes
    ):
        raise AIDirectorError(
            "AI Director did not create any scenes."
        )

    for index, raw_scene in enumerate(
        scenes,
        start=1,
    ):
        scene = _normalize_scene(
            raw_scene
        )

        if not scene["script"]:
            raise AIDirectorError(
                f"Scene {index} has no script."
            )

        if _is_placeholder(
            scene["script"]
        ):
            raise AIDirectorError(
                f"Scene {index} contains placeholder script text."
            )

        if _is_placeholder(
            scene["action"]
        ):
            raise AIDirectorError(
                f"Scene {index} contains placeholder action text."
            )

        if _is_placeholder(
            scene["environment"]
        ):
            raise AIDirectorError(
                f"Scene {index} contains placeholder environment text."
            )

        if _is_placeholder(
            scene["camera"]
        ):
            raise AIDirectorError(
                f"Scene {index} contains placeholder camera text."
            )

        if _is_placeholder(
            scene["transition"]
        ):
            raise AIDirectorError(
                f"Scene {index} contains placeholder transition text."
            )


def get_user_avatars(
    db: Session,
    user_id: int,
) -> list[dict[str, Any]]:

    avatars = (
        db.query(Avatar)
        .filter(
            Avatar.user_id == user_id
        )
        .order_by(
            Avatar.id.asc()
        )
        .all()
    )

    return [
        {
            "id": avatar.id,
            "name": avatar.name,
            "image_url": avatar.image_url,
        }
        for avatar in avatars
    ]


def get_user_voices(
    db: Session,
    user_id: int,
) -> list[dict[str, Any]]:

    voices = (
        db.query(Voice)
        .filter(
            Voice.user_id == user_id,
            Voice.status == "ready",
        )
        .order_by(
            Voice.id.asc()
        )
        .all()
    )

    return [
        {
            "id": voice.id,
            "name": voice.name,
            "voice_type": voice.voice_type,
            "provider_voice_id": (
                voice.provider_voice_id
            ),
            "status": voice.status,
        }
        for voice in voices
    ]


def _pick_auto_builtin_voice(
    builtin_voices: list[
        dict[str, Any]
    ],
) -> str:

    usable = [
        voice
        for voice in builtin_voices
        if voice.get("tts_voice")
    ]

    if not usable:
        return ""

    preferred = next(
        (
            voice
            for voice in usable
            if voice.get("language") == "en"
            and str(
                voice.get(
                    "gender",
                    "",
                )
            ).lower()
            == "female"
        ),
        None,
    )

    if preferred:
        return preferred[
            "tts_voice"
        ]

    english = next(
        (
            voice
            for voice in usable
            if voice.get("language") == "en"
        ),
        None,
    )

    return (
        english["tts_voice"]
        if english
        else usable[0]["tts_voice"]
    )


def _build_director_prompt(
    idea: str,
    avatars: list[dict[str, Any]],
    selected_voice_description: str,
    selected_avatar_description: str,
) -> str:

    avatar_text = json.dumps(
        avatars,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
You are Aloko AI Director, a professional video-production planner.

Transform the user's idea into a complete, editable AI video project.

USER IDEA:
{idea}

AVAILABLE USER AVATARS:
{avatar_text}

VOICE INSTRUCTION:
{selected_voice_description}

AVATAR INSTRUCTION:
{selected_avatar_description}

PRODUCTION RULES:
1. Return ONLY valid JSON. No markdown. No commentary.
2. Create a meaningful professional project title based on the user's idea.
3. Create a short useful project description based on the user's idea.
4. Decide the number of scenes dynamically. Do not always create five or ten scenes.
5. Short ideas may need 2-4 scenes. Longer videos may need more scenes.
6. Every scene must contain original spoken narration directly related to the idea.
7. Never output placeholder phrases such as "Professional project name", "Narration for this scene", "Specific presenter action", or "Camera direction".
8. Camera, action, environment and transition must describe the actual scene.
9. Captions should normally be enabled.
10. Background music must be a descriptive music direction, never a fake filename or file path.
11. Keep scripts natural for spoken narration.
12. The complete result must be editable later in Aloko Creator Studio.
13. Do not invent avatar IDs. Only use IDs from AVAILABLE USER AVATARS.
14. Do not invent voice IDs or voice names. Voice selection is supplied by the application.
15. Do not put explanations outside the JSON object.

OUTPUT SHAPE:
{{
  "project": {{
    "name": "A real title based on the idea",
    "description": "A useful short description"
  }},
  "scenes": [
    {{
      "script": "Actual narration for this scene",
      "avatar_id": null,
      "voice_id": null,
      "voice": "",
      "action": "Actual presenter action for this scene",
      "environment": "Actual environment for this scene",
      "camera": "Actual camera direction for this scene",
      "transition": "Actual transition",
      "captions_enabled": true,
      "background_music": "Actual music direction"
    }}
  ]
}}
""".strip()


def _apply_voice_choice(
    scenes: list[dict[str, Any]],
    voice_mode: str,
    voice_id: int | None,
    builtin_voice: str | None,
    custom_voices: list[dict[str, Any]],
    builtin_voices: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    str,
    int | None,
    str,
]:

    if voice_mode == "personal":

        valid = next(
            (
                voice
                for voice in custom_voices
                if voice["id"] == voice_id
            ),
            None,
        )

        if not valid:
            raise AIDirectorError(
                "The selected personal voice is not available or is not ready."
            )

        selected_id = valid["id"]

        selected_name = (
            valid.get("name")
            or "Personal voice"
        )

        for scene in scenes:
            scene["voice_id"] = selected_id
            scene["voice"] = ""

        return (
            scenes,
            "personal",
            selected_id,
            selected_name,
        )

    if voice_mode == "builtin":

        valid_names = {
            voice.get("tts_voice")
            for voice in builtin_voices
            if voice.get("tts_voice")
        }

        if (
            not builtin_voice
            or builtin_voice not in valid_names
        ):
            raise AIDirectorError(
                "The selected Aloko voice is not available."
            )

        for scene in scenes:
            scene["voice_id"] = None
            scene["voice"] = builtin_voice

        return (
            scenes,
            "builtin",
            None,
            builtin_voice,
        )

    if voice_mode == "none":

        for scene in scenes:
            scene["voice_id"] = None
            scene["voice"] = ""

        return (
            scenes,
            "none",
            None,
            "",
        )

    chosen = _pick_auto_builtin_voice(
        builtin_voices
    )

    for scene in scenes:
        scene["voice_id"] = None
        scene["voice"] = chosen

    return (
        scenes,
        "auto",
        None,
        chosen,
    )


def _apply_avatar_choice(
    scenes: list[dict[str, Any]],
    avatar_mode: str,
    avatar_id: int | None,
    avatars: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    str,
    int | None,
]:

    valid_ids = {
        avatar["id"]
        for avatar in avatars
    }

    if avatar_mode == "selected":

        if (
            avatar_id is None
            or avatar_id not in valid_ids
        ):
            raise AIDirectorError(
                "The selected avatar is not available."
            )

        for scene in scenes:
            scene["avatar_id"] = avatar_id

        return (
            scenes,
            "selected",
            avatar_id,
        )

    if avatar_mode == "none":

        for scene in scenes:
            scene["avatar_id"] = None

        return (
            scenes,
            "none",
            None,
        )

    selected = (
        avatars[0]["id"]
        if avatars
        else None
    )

    for scene in scenes:
        scene["avatar_id"] = selected

    return (
        scenes,
        "auto",
        selected,
    )


async def generate_director_plan(
    idea: str,
    db: Session,
    user_id: int,
    voice_mode: str = "auto",
    voice_id: int | None = None,
    builtin_voice: str | None = None,
    avatar_mode: str = "auto",
    avatar_id: int | None = None,
) -> dict[str, Any]:

    idea = idea.strip()

    if not idea:
        raise AIDirectorError(
            "Video idea cannot be empty."
        )

    if len(idea) > 10000:
        raise AIDirectorError(
            "Video idea is too long. Maximum 10000 characters."
        )

    avatars = get_user_avatars(
        db=db,
        user_id=user_id,
    )

    custom_voices = get_user_voices(
        db=db,
        user_id=user_id,
    )

    try:
        from app.services.voice_catalog import (
            get_all_voices,
        )

        builtin_voices = await get_all_voices()

    except Exception as exc:
        raise AIDirectorError(
            f"Failed to load built-in voices: {str(exc)}"
        ) from exc

    if not isinstance(
        builtin_voices,
        list,
    ):
        builtin_voices = []

    # --------------------------------------------------------
    # VOICE SELECTION
    # --------------------------------------------------------

    if voice_mode == "personal":

        selected_personal = next(
            (
                voice
                for voice in custom_voices
                if voice["id"] == voice_id
            ),
            None,
        )

        if not selected_personal:
            raise AIDirectorError(
                "The selected personal voice is not available or is not ready."
            )

        voice_description = (
            "Use the user's personal voice "
            f"with database ID {selected_personal['id']} "
            f"({selected_personal.get('name') or 'Personal voice'})."
        )

    elif voice_mode == "builtin":

        valid_names = {
            voice.get("tts_voice")
            for voice in builtin_voices
            if voice.get("tts_voice")
        }

        if (
            not builtin_voice
            or builtin_voice not in valid_names
        ):
            raise AIDirectorError(
                "The selected Aloko voice is not available."
            )

        voice_description = (
            "Use this exact Aloko built-in voice: "
            f"{builtin_voice}."
        )

    elif voice_mode == "none":

        voice_description = (
            "Do not assign a voice yet. "
            "Leave voice fields empty/null."
        )

    else:

        voice_description = (
            "Let the application choose the voice "
            "automatically after planning. "
            "Do not invent a voice name."
        )

    # --------------------------------------------------------
    # AVATAR SELECTION
    # --------------------------------------------------------

    if avatar_mode == "selected":

        selected_avatar = next(
            (
                avatar
                for avatar in avatars
                if avatar["id"] == avatar_id
            ),
            None,
        )

        if not selected_avatar:
            raise AIDirectorError(
                "The selected avatar is not available."
            )

        avatar_description = (
            "Use this exact user avatar ID "
            f"{selected_avatar['id']} "
            f"({selected_avatar.get('name') or 'User avatar'}) "
            "for every scene."
        )

    elif avatar_mode == "none":

        avatar_description = (
            "Do not assign an avatar yet. "
            "Leave avatar_id null."
        )

    elif avatars:

        avatar_description = (
            "The application will automatically "
            "use an available user avatar."
        )

    else:

        avatar_description = (
            "No user avatar is currently available. "
            "Leave avatar_id null."
        )

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    prompt = _build_director_prompt(
        idea=idea,
        avatars=avatars,
        selected_voice_description=(
            voice_description
        ),
        selected_avatar_description=(
            avatar_description
        ),
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are Aloko AI Director. "
                "Return a complete, realistic "
                "video plan as valid JSON only. "
                "Never use placeholders."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    # --------------------------------------------------------
    # FIRST AI REQUEST
    # --------------------------------------------------------

    try:

        response = client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            format="json",
            options={
                "temperature": 0.35,
            },
        )

    except Exception as exc:

        raise AIDirectorError(
            "AI Director could not connect to "
            f"Ollama: {str(exc)}"
        ) from exc

    raw_content = (
        response
        .get("message", {})
        .get("content", "")
    )

    # --------------------------------------------------------
    # VALIDATE AI RESPONSE
    # --------------------------------------------------------

    try:

        plan = _extract_json(
            raw_content
        )

        _validate_plan_content(
            plan
        )

    except AIDirectorError as first_error:

        correction_messages = (
            messages
            + [
                {
                    "role": "user",
                    "content": (
                        "Your previous response was rejected "
                        "because it contained a placeholder "
                        "or invalid field: "
                        f"{first_error}. "
                        "Rewrite the entire JSON project now. "
                        "Use real, idea-specific narration "
                        "and production directions. "
                        "Do not mention the correction. "
                        "Return JSON only."
                    ),
                }
            ]
        )

        try:

            retry_response = client.chat(
                model=OLLAMA_MODEL,
                messages=correction_messages,
                format="json",
                options={
                    "temperature": 0.25,
                },
            )

            plan = _extract_json(
                retry_response
                .get("message", {})
                .get("content", "")
            )

            _validate_plan_content(
                plan
            )

        except Exception as retry_error:

            raise AIDirectorError(
                "AI Director could not create "
                f"a valid project: {retry_error}"
            ) from retry_error

    # --------------------------------------------------------
    # PROJECT DATA
    # --------------------------------------------------------

    project_data = plan.get(
        "project",
        {},
    )

    project_name = _clean_text(
        project_data.get("name"),
        default="AI Director Project",
    )

    project_description = _clean_text(
        project_data.get(
            "description"
        )
    )

    raw_scenes = plan.get(
        "scenes",
        [],
    )

    if (
        not isinstance(
            raw_scenes,
            list,
        )
        or not raw_scenes
    ):
        raise AIDirectorError(
            "AI Director did not return a valid scene list."
        )

    # --------------------------------------------------------
    # NORMALIZE SCENES
    # --------------------------------------------------------

    scenes: list[
        dict[str, Any]
    ] = []

    valid_avatar_ids = {
        avatar["id"]
        for avatar in avatars
    }

    valid_custom_voice_ids = {
        voice["id"]
        for voice in custom_voices
    }

    valid_builtin_voice_names = {
        voice.get("tts_voice")
        for voice in builtin_voices
        if voice.get("tts_voice")
    }

    for index, raw_scene in enumerate(
        raw_scenes,
        start=1,
    ):

        scene = _normalize_scene(
            raw_scene
        )

        if (
            not scene["script"]
            or _is_placeholder(
                scene["script"]
            )
        ):
            raise AIDirectorError(
                f"Scene {index} has invalid narration."
            )

        # ----------------------------------------------------
        # Validate avatar
        # ----------------------------------------------------

        if (
            scene["avatar_id"]
            is not None
            and scene["avatar_id"]
            not in valid_avatar_ids
        ):
            scene["avatar_id"] = None

        # ----------------------------------------------------
        # Validate personal voice
        # ----------------------------------------------------

        if (
            scene["voice_id"]
            is not None
            and scene["voice_id"]
            not in valid_custom_voice_ids
        ):
            scene["voice_id"] = None

        # ----------------------------------------------------
        # Validate built-in voice
        # ----------------------------------------------------

        if (
            scene["voice"]
            and scene["voice"]
            not in valid_builtin_voice_names
        ):
            scene["voice"] = ""

        # ----------------------------------------------------
        # Production defaults
        # ----------------------------------------------------

        if (
            not scene["action"]
            or _is_placeholder(
                scene["action"]
            )
        ):
            scene["action"] = (
                "Presenter delivers the narration "
                "naturally and confidently."
            )

        if (
            not scene["environment"]
            or _is_placeholder(
                scene["environment"]
            )
        ):
            scene["environment"] = (
                "A clean, visually relevant "
                "production setting."
            )

        if (
            not scene["camera"]
            or _is_placeholder(
                scene["camera"]
            )
        ):
            scene["camera"] = (
                "Medium shot at eye level "
                "with a subtle cinematic push-in."
            )

        if (
            not scene["transition"]
            or _is_placeholder(
                scene["transition"]
            )
        ):
            scene["transition"] = "Cut"

        if (
            not scene["background_music"]
            or _is_placeholder(
                scene["background_music"]
            )
        ):
            scene["background_music"] = (
                "Subtle cinematic background music "
                "matching the mood."
            )

        scene["captions_enabled"] = True

        scenes.append(scene)

    # --------------------------------------------------------
    # APPLY VOICE CHOICE
    # --------------------------------------------------------

    (
        scenes,
        resolved_voice_mode,
        resolved_voice_id,
        resolved_voice,
    ) = _apply_voice_choice(
        scenes,
        voice_mode,
        voice_id,
        builtin_voice,
        custom_voices,
        builtin_voices,
    )

    # --------------------------------------------------------
    # APPLY AVATAR CHOICE
    # --------------------------------------------------------

    (
        scenes,
        resolved_avatar_mode,
        resolved_avatar_id,
    ) = _apply_avatar_choice(
        scenes,
        avatar_mode,
        avatar_id,
        avatars,
    )

    # --------------------------------------------------------
    # RETURN FINAL PLAN
    # --------------------------------------------------------

    return {
        "project": {
            "name": project_name,
            "description": project_description,
        },

        "scenes": scenes,

        "metadata": {
            "avatar_count": len(
                avatars
            ),

            "custom_voice_count": len(
                custom_voices
            ),

            "builtin_voice_count": len(
                builtin_voices
            ),

            "scene_count": len(
                scenes
            ),

            "model": OLLAMA_MODEL,

            "voice_mode": (
                resolved_voice_mode
            ),

            "voice_id": (
                resolved_voice_id
            ),

            "voice": (
                resolved_voice
            ),

            "avatar_mode": (
                resolved_avatar_mode
            ),

            "avatar_id": (
                resolved_avatar_id
            ),
        },
    }