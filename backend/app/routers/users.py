"""User profile and preferences router."""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserPreference
from app.core.dependencies import get_current_active_user
from app.schemas.auth import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


class PreferenceUpdate(BaseModel):
    """Schema for updating user preferences."""
    preferred_subjects: Optional[List[str]] = None
    default_answer_style: Optional[str] = Field(None, pattern="^(detailed|concise|simple|beginner|exam_prep|step_by_step)$")
    learning_goals: Optional[str] = None


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the current user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile (full_name)."""
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
        db.commit()
        db.refresh(current_user)
    return current_user


@router.get("/me/preferences")
def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return the current user's preferences."""
    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    if not prefs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        )

    return {
        "preferred_subjects": json.loads(prefs.preferred_subjects or "[]"),
        "default_answer_style": prefs.default_answer_style,
        "learning_goals": prefs.learning_goals,
    }


@router.put("/me/preferences")
def update_preferences(
    prefs_data: PreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update the current user's preferences."""
    prefs = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == current_user.id)
        .first()
    )
    if not prefs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        )

    if prefs_data.preferred_subjects is not None:
        prefs.preferred_subjects = json.dumps(prefs_data.preferred_subjects)
    if prefs_data.default_answer_style is not None:
        prefs.default_answer_style = prefs_data.default_answer_style
    if prefs_data.learning_goals is not None:
        prefs.learning_goals = prefs_data.learning_goals

    db.commit()

    return {
        "preferred_subjects": json.loads(prefs.preferred_subjects or "[]"),
        "default_answer_style": prefs.default_answer_style,
        "learning_goals": prefs.learning_goals,
    }
