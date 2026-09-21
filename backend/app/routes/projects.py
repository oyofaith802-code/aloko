from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import get_current_user

from app.models.user import User
from app.models.creator_project import CreatorProject
from app.models.creator_scene import CreatorScene


router = APIRouter(
    prefix="/projects",
    tags=["Creator Projects"],
)


# ==========================================================
# SCHEMAS
# ==========================================================

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SceneCreate(BaseModel):
    script: Optional[str] = None

    # Avatar / voice
    avatar_id: Optional[int] = None
    voice_id: Optional[int] = None
    voice: Optional[str] = None

    # Professional scene controls
    action: Optional[str] = None
    environment: Optional[str] = None
    camera: Optional[str] = None
    transition: Optional[str] = None

    # Audio / captions
    captions_enabled: bool = True
    background_music: Optional[str] = None

    # Optional explicit scene ordering
    scene_order: Optional[int] = None


class SceneUpdate(BaseModel):
    script: Optional[str] = None

    # Avatar / voice
    avatar_id: Optional[int] = None
    voice_id: Optional[int] = None
    voice: Optional[str] = None

    # Professional scene controls
    action: Optional[str] = None
    environment: Optional[str] = None
    camera: Optional[str] = None
    transition: Optional[str] = None

    # Audio / captions
    captions_enabled: Optional[bool] = None
    background_music: Optional[str] = None

    # Scene ordering
    scene_order: Optional[int] = None


# ==========================================================
# HELPER
# ==========================================================

def get_owned_project(
    project_id: int,
    user: User,
    db: Session,
):
    project = (
        db.query(CreatorProject)
        .filter(
            CreatorProject.id == project_id,
            CreatorProject.user_id == user.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


def scene_to_dict(scene: CreatorScene):
    """
    Convert a CreatorScene database object into a consistent API response.
    """

    return {
        "id": scene.id,
        "project_id": scene.project_id,
        "scene_order": scene.scene_order,
        "script": scene.script,

        "avatar_id": scene.avatar_id,

        # Personal/custom voice
        "voice_id": scene.voice_id,

        # Built-in AI voice
        "voice": scene.voice,

        # Professional scene controls
        "action": scene.action,
        "environment": scene.environment,
        "camera": scene.camera,
        "transition": scene.transition,

        # Captions / music
        "captions_enabled": scene.captions_enabled,
        "background_music": scene.background_music,

        "created_at": scene.created_at,
        "updated_at": scene.updated_at,
    }


# ==========================================================
# CREATE PROJECT
# ==========================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = CreatorProject(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        status="draft",
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


# ==========================================================
# LIST MY PROJECTS
# ==========================================================

@router.get("")
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(CreatorProject)
        .filter(
            CreatorProject.user_id == current_user.id
        )
        .order_by(
            CreatorProject.updated_at.desc()
        )
        .all()
    )

    return [
        {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        for project in projects
    ]


# ==========================================================
# GET ONE PROJECT
# ==========================================================

@router.get("/{project_id}")
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(
        project_id,
        current_user,
        db,
    )

    scenes = (
        db.query(CreatorScene)
        .filter(
            CreatorScene.project_id == project.id
        )
        .order_by(
            CreatorScene.scene_order.asc()
        )
        .all()
    )

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "scenes": [
            scene_to_dict(scene)
            for scene in scenes
        ],
    }


# ==========================================================
# UPDATE PROJECT
# ==========================================================

@router.patch("/{project_id}")
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(
        project_id,
        current_user,
        db,
    )

    if data.name is not None:
        project.name = data.name

    if data.description is not None:
        project.description = data.description

    if data.status is not None:
        project.status = data.status

    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


# ==========================================================
# DELETE PROJECT
# ==========================================================

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(
        project_id,
        current_user,
        db,
    )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully."
    }


# ==========================================================
# CREATE SCENE
# ==========================================================

@router.post(
    "/{project_id}/scenes",
    status_code=status.HTTP_201_CREATED,
)
def create_scene(
    project_id: int,
    data: SceneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(
        project_id,
        current_user,
        db,
    )

    # ------------------------------------------------------
    # Determine scene order
    # ------------------------------------------------------

    if data.scene_order is not None and data.scene_order > 0:
        next_order = data.scene_order

        # Shift existing scenes if necessary
        existing_scenes = (
            db.query(CreatorScene)
            .filter(
                CreatorScene.project_id == project.id,
                CreatorScene.scene_order >= next_order,
            )
            .order_by(
                CreatorScene.scene_order.desc()
            )
            .all()
        )

        for existing_scene in existing_scenes:
            existing_scene.scene_order += 1

    else:
        last_scene = (
            db.query(CreatorScene)
            .filter(
                CreatorScene.project_id == project.id
            )
            .order_by(
                CreatorScene.scene_order.desc()
            )
            .first()
        )

        next_order = (
            last_scene.scene_order + 1
            if last_scene
            else 1
        )

    # ------------------------------------------------------
    # Create scene
    # ------------------------------------------------------

    scene = CreatorScene(
        project_id=project.id,
        scene_order=next_order,

        script=data.script,

        avatar_id=data.avatar_id,

        # Personal/custom voice
        voice_id=data.voice_id,

        # Built-in AI voice
        voice=data.voice,

        # Professional controls
        action=data.action,
        environment=data.environment,
        camera=data.camera,
        transition=data.transition,

        # Captions / music
        captions_enabled=data.captions_enabled,
        background_music=data.background_music,
    )

    db.add(scene)

    # Mark project as having unsaved/editable creator content
    project.status = "draft"

    db.commit()
    db.refresh(scene)

    return scene_to_dict(scene)


# ==========================================================
# UPDATE SCENE
# ==========================================================

@router.patch(
    "/{project_id}/scenes/{scene_id}"
)
def update_scene(
    project_id: int,
    scene_id: int,
    data: SceneUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(
        project_id,
        current_user,
        db,
    )

    scene = (
        db.query(CreatorScene)
        .filter(
            CreatorScene.id == scene_id,
            CreatorScene.project_id == project.id,
        )
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found.",
        )

    updates = data.model_dump(
        exclude_unset=True
    )

    # ------------------------------------------------------
    # Handle scene ordering safely
    # ------------------------------------------------------

    if "scene_order" in updates:
        new_order = updates.pop("scene_order")

        if new_order is not None and new_order > 0:
            old_order = scene.scene_order

            if new_order != old_order:

                if new_order < old_order:
                    affected_scenes = (
                        db.query(CreatorScene)
                        .filter(
                            CreatorScene.project_id == project.id,
                            CreatorScene.scene_order >= new_order,
                            CreatorScene.scene_order < old_order,
                            CreatorScene.id != scene.id,
                        )
                        .all()
                    )

                    for affected_scene in affected_scenes:
                        affected_scene.scene_order += 1

                else:
                    affected_scenes = (
                        db.query(CreatorScene)
                        .filter(
                            CreatorScene.project_id == project.id,
                            CreatorScene.scene_order <= new_order,
                            CreatorScene.scene_order > old_order,
                            CreatorScene.id != scene.id,
                        )
                        .all()
                    )

                    for affected_scene in affected_scenes:
                        affected_scene.scene_order -= 1

                scene.scene_order = new_order

    # ------------------------------------------------------
    # Apply normal updates
    # ------------------------------------------------------

    for field, value in updates.items():
        setattr(scene, field, value)

    project.status = "draft"

    db.commit()
    db.refresh(scene)

    return scene_to_dict(scene)


# ==========================================================
# DELETE SCENE
# ==========================================================

@router.delete(
    "/{project_id}/scenes/{scene_id}"
)
def delete_scene(
    project_id: int,
    scene_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(
        project_id,
        current_user,
        db,
    )

    scene = (
        db.query(CreatorScene)
        .filter(
            CreatorScene.id == scene_id,
            CreatorScene.project_id == project.id,
        )
        .first()
    )

    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found.",
        )

    deleted_order = scene.scene_order

    db.delete(scene)
    db.flush()

    # ------------------------------------------------------
    # Close the ordering gap
    # ------------------------------------------------------

    remaining_scenes = (
        db.query(CreatorScene)
        .filter(
            CreatorScene.project_id == project.id,
            CreatorScene.scene_order > deleted_order,
        )
        .all()
    )

    for remaining_scene in remaining_scenes:
        remaining_scene.scene_order -= 1

    project.status = "draft"

    db.commit()

    return {
        "message": "Scene deleted successfully."
    }