from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..config.database import pocketbase
from ..models.templates import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateExerciseCreate, TemplateExerciseResponse
)
from api.auth.auth_bearer import JWTBearer
import datetime

router = APIRouter()


# ── TEMPLATE ROUTES ───────────────────────────────────────────────────────────

@router.get("/templates/", response_model=List[TemplateResponse], dependencies=[Depends(JWTBearer())])
async def list_templates(current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        result  = pocketbase.table("workout_templates", token=token).eq("user_id", user_id).execute()
        items   = result.get("items", [])
        items.sort(key=lambda x: x.get("last_used_at") or x.get("created", ""), reverse=True)
        return items
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/", response_model=TemplateResponse, dependencies=[Depends(JWTBearer())])
async def create_template(template: TemplateCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        data = {
            "user_id":                user_id,
            "name":                   template.name,
            "workout_type":           template.workout_type or "",
            "estimated_duration_min": template.estimated_duration_min or 45,
            "difficulty":             template.difficulty or "intermediate",
            "description":            template.description or "",
        }
        result = pocketbase.table("workout_templates", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to create template")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/{template_id}/", dependencies=[Depends(JWTBearer())])
async def get_template(template_id: str, current_user: dict = Depends(JWTBearer())):
    """Returns template info + exercises list."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        t_result = pocketbase.table("workout_templates", token=token).eq("id", template_id).eq("user_id", user_id).execute()
        if not t_result.get("items"):
            raise HTTPException(status_code=404, detail="Template not found")
        template = t_result["items"][0]

        ex_result = pocketbase.table("template_exercises", token=token).eq("template_id", template_id).execute()
        exercises = sorted(ex_result.get("items", []), key=lambda x: x.get("order_index", 0))

        return {**template, "exercises": exercises}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/templates/{template_id}/", response_model=TemplateResponse, dependencies=[Depends(JWTBearer())])
async def update_template(template_id: str, template: TemplateUpdate, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        # Verify ownership
        check = pocketbase.table("workout_templates", token=token).eq("id", template_id).eq("user_id", user_id).execute()
        if not check.get("items"):
            raise HTTPException(status_code=404, detail="Template not found")

        data = {"id": template_id}
        if template.name is not None:                   data["name"] = template.name
        if template.workout_type is not None:           data["workout_type"] = template.workout_type
        if template.estimated_duration_min is not None: data["estimated_duration_min"] = template.estimated_duration_min
        if template.difficulty is not None:             data["difficulty"] = template.difficulty
        if template.description is not None:            data["description"] = template.description

        result = pocketbase.table("workout_templates", token=token).update(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to update template")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}/", dependencies=[Depends(JWTBearer())])
async def delete_template(template_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        pocketbase.table("workout_templates", token=token).eq("id", template_id).eq("user_id", user_id).delete()
        # Delete exercises too
        pocketbase.table("template_exercises", token=token).eq("template_id", template_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── TEMPLATE EXERCISES ────────────────────────────────────────────────────────

@router.post("/templates/{template_id}/exercises/",
             response_model=TemplateExerciseResponse, dependencies=[Depends(JWTBearer())])
async def add_exercise_to_template(
    template_id: str,
    exercise: TemplateExerciseCreate,
    current_user: dict = Depends(JWTBearer())
):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        # Verify template ownership
        check = pocketbase.table("workout_templates", token=token).eq("id", template_id).eq("user_id", user_id).execute()
        if not check.get("items"):
            raise HTTPException(status_code=404, detail="Template not found")

        data = {
            "template_id":         template_id,
            "exercise_library_id": exercise.exercise_library_id,
            "exercise_name":       exercise.exercise_name,
            "order_index":         exercise.order_index,
            "target_sets":         exercise.target_sets or 3,
            "target_reps":         exercise.target_reps or 10,
            "target_weight_kg":    exercise.target_weight_kg or 0.0,
            "rest_seconds":        exercise.rest_seconds or 90,
        }
        result = pocketbase.table("template_exercises", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to add exercise")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/templates/{template_id}/exercises/{exercise_id}/",
            response_model=TemplateExerciseResponse, dependencies=[Depends(JWTBearer())])
async def update_template_exercise(
    template_id: str,
    exercise_id: str,
    exercise: TemplateExerciseCreate,
    current_user: dict = Depends(JWTBearer())
):
    try:
        token = current_user.get("_token")
        data  = {
            "id":                  exercise_id,
            "exercise_library_id": exercise.exercise_library_id,
            "exercise_name":       exercise.exercise_name,
            "order_index":         exercise.order_index,
            "target_sets":         exercise.target_sets or 3,
            "target_reps":         exercise.target_reps or 10,
            "target_weight_kg":    exercise.target_weight_kg or 0.0,
            "rest_seconds":        exercise.rest_seconds or 90,
        }
        result = pocketbase.table("template_exercises", token=token).update(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to update exercise")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}/exercises/{exercise_id}/", dependencies=[Depends(JWTBearer())])
async def remove_exercise_from_template(
    template_id: str,
    exercise_id: str,
    current_user: dict = Depends(JWTBearer())
):
    try:
        token = current_user.get("_token")
        pocketbase.table("template_exercises", token=token).eq("id", exercise_id).eq("template_id", template_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
