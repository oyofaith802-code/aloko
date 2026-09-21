from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.creator_project import CreatorProject
from app.models.creator_scene import CreatorScene
from app.services.ai_director import (
    generate_director_plan,
    AIDirectorError,
)

router = APIRouter(
    prefix="/ai-director",
    tags=["AI Director"],
)


class AIDirectorRequest(BaseModel):
    idea: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    voice_mode: Literal[
        "personal",
        "builtin",
        "auto",
        "none",
    ] = "auto"

    voice_id: int | None = None

    builtin_voice: str | None = None

    avatar_mode: Literal[
        "selected",
        "auto",
        "none",
    ] = "auto"

    avatar_id: int | None = None


@router.post("/generate")
async def generate_ai_director_project(
    data: AIDirectorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        plan = await generate_director_plan(
            idea=data.idea,
            db=db,
            user_id=current_user.id,
            voice_mode=data.voice_mode,
            voice_id=data.voice_id,
            builtin_voice=data.builtin_voice,
            avatar_mode=data.avatar_mode,
            avatar_id=data.avatar_id,
        )

        project_data = plan.get(
            "project",
            {},
        )

        scenes = plan.get(
            "scenes",
            [],
        )

        if not scenes:
            raise AIDirectorError(
                "AI Director did not create any scenes."
            )

        project = CreatorProject(
            user_id=current_user.id,
            name=project_data.get(
                "name",
                "AI Director Project",
            ),
            description=project_data.get(
                "description"
            ),
            status="draft",
        )

        db.add(project)
        db.flush()

        created_scenes = []

        for index, scene_data in enumerate(
            scenes,
            start=1,
        ):
            scene = CreatorScene(
                project_id=project.id,
                scene_order=index,
                script=scene_data.get(
                    "script"
                ),
                avatar_id=scene_data.get(
                    "avatar_id"
                ),
                voice_id=scene_data.get(
                    "voice_id"
                ),
                voice=scene_data.get(
                    "voice"
                ),
                action=scene_data.get(
                    "action"
                ),
                environment=scene_data.get(
                    "environment"
                ),
                camera=scene_data.get(
                    "camera"
                ),
                transition=scene_data.get(
                    "transition"
                ),
                captions_enabled=scene_data.get(
                    "captions_enabled",
                    True,
                ),
                background_music=scene_data.get(
                    "background_music"
                ),
            )

            db.add(scene)
            created_scenes.append(scene)

        db.commit()
        db.refresh(project)

        for scene in created_scenes:
            db.refresh(scene)

        return {
            "success": True,
            "message": (
                "AI Director created your "
                "project successfully."
            ),

            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
            },

            "scenes": [
                {
                    "id": scene.id,
                    "project_id": scene.project_id,
                    "scene_order": scene.scene_order,
                    "script": scene.script,
                    "avatar_id": scene.avatar_id,
                    "voice_id": scene.voice_id,
                    "voice": scene.voice,
                    "action": scene.action,
                    "environment": scene.environment,
                    "camera": scene.camera,
                    "transition": scene.transition,
                    "captions_enabled": (
                        scene.captions_enabled
                    ),
                    "background_music": (
                        scene.background_music
                    ),
                }
                for scene in created_scenes
            ],

            "metadata": plan.get(
                "metadata",
                {},
            ),
        }

    except AIDirectorError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"AI Director failed: {str(exc)}",
        ) from exc