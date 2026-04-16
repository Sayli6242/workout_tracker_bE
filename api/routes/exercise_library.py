from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from ..config.database import pocketbase
from ..models.exercise_library import ExerciseLibraryCreate, ExerciseLibraryResponse
from ..data.exercise_seed import SEED_EXERCISES
from api.auth.auth_bearer import JWTBearer

router = APIRouter()


def _exercise_matches(ex: dict, search: Optional[str], muscle_group: Optional[str],
                      equipment: Optional[str], difficulty: Optional[str]) -> bool:
    if search and search.lower() not in ex["name"].lower():
        return False
    if muscle_group and ex["muscle_group"] != muscle_group:
        return False
    if equipment and ex["equipment"] != equipment:
        return False
    if difficulty and ex["difficulty"] != difficulty:
        return False
    return True


# ── EXERCISE LIBRARY ROUTES ───────────────────────────────────────────────────

@router.get("/exercise-library/", dependencies=[Depends(JWTBearer())])
async def list_exercises(
    current_user: dict = Depends(JWTBearer()),
    search:       Optional[str] = Query(None),
    muscle_group: Optional[str] = Query(None),
    equipment:    Optional[str] = Query(None),
    difficulty:   Optional[str] = Query(None),
):
    """Return seed exercises + user's custom exercises, with optional filters."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        # Filter seed exercises
        filtered = [
            {**ex, "is_custom": False, "created_by": None}
            for ex in SEED_EXERCISES
            if _exercise_matches(ex, search, muscle_group, equipment, difficulty)
        ]

        # Fetch user's custom exercises from PocketBase
        try:
            result = pocketbase.table("custom_exercises", token=token).eq("created_by", user_id).execute()
            custom = result.get("items", [])
            custom_filtered = [
                {**ex, "is_custom": True}
                for ex in custom
                if _exercise_matches(ex, search, muscle_group, equipment, difficulty)
            ]
            filtered.extend(custom_filtered)
        except Exception:
            pass  # custom_exercises collection may not exist yet

        return filtered
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exercise-library/{exercise_id}/", dependencies=[Depends(JWTBearer())])
async def get_exercise(exercise_id: str, current_user: dict = Depends(JWTBearer())):
    """Get a single exercise by id (seed or custom)."""
    # Check seed first
    for ex in SEED_EXERCISES:
        if ex["id"] == exercise_id:
            return {**ex, "is_custom": False, "created_by": None}

    # Check custom exercises
    try:
        token  = current_user.get("_token")
        result = pocketbase.table("custom_exercises", token=token).eq("id", exercise_id).execute()
        items  = result.get("items", [])
        if items:
            return {**items[0], "is_custom": True}
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Exercise not found")


@router.post("/exercise-library/custom/", response_model=ExerciseLibraryResponse,
             dependencies=[Depends(JWTBearer())])
async def create_custom_exercise(
    exercise: ExerciseLibraryCreate,
    current_user: dict = Depends(JWTBearer())
):
    """Create a user-defined custom exercise."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        data = {
            "name":              exercise.name,
            "muscle_group":      exercise.muscle_group.value,
            "secondary_muscles": exercise.secondary_muscles or "",
            "equipment":         exercise.equipment.value,
            "category":          exercise.category.value,
            "difficulty":        exercise.difficulty.value,
            "description":       exercise.description or "",
            "instructions":      exercise.instructions or "",
            "is_custom":         True,
            "created_by":        user_id,
        }
        result = pocketbase.table("custom_exercises", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to create exercise")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/exercise-library/custom/{exercise_id}/", dependencies=[Depends(JWTBearer())])
async def delete_custom_exercise(exercise_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        pocketbase.table("custom_exercises", token=token).eq("id", exercise_id).eq("created_by", user_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exercise-library/muscle-groups/", dependencies=[Depends(JWTBearer())])
async def list_muscle_groups():
    """Return unique muscle groups from seed data."""
    groups = sorted(set(ex["muscle_group"] for ex in SEED_EXERCISES))
    return groups


@router.get("/exercise-library/equipment-list/", dependencies=[Depends(JWTBearer())])
async def list_equipment():
    """Return unique equipment types from seed data."""
    equip = sorted(set(ex["equipment"] for ex in SEED_EXERCISES))
    return equip
