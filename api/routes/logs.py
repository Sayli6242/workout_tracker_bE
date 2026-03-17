from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..config.database import pocketbase
from ..models.logs import (
    ExerciseLogCreate, ExerciseLogResponse,
    WorkoutLogCreate, WorkoutLogResponse,
    PRResponse
)
from api.auth.auth_bearer import JWTBearer
import datetime

router = APIRouter()


# ── EXERCISE LOG ROUTES ───────────────────────────────────────────────────────

@router.post("/exercise-logs/", response_model=ExerciseLogResponse, dependencies=[Depends(JWTBearer())])
async def create_exercise_log(log: ExerciseLogCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        data = {
            "user_id": user_id,
            "exercise_id": log.exercise_id,
            "sets": log.sets,
            "reps": log.reps,
            "weight_kg": log.weight_kg,
            "notes": log.notes or "",
            "logged_at": log.logged_at or datetime.datetime.utcnow().isoformat() + "Z",
        }
        result = pocketbase.table("exercise_logs", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail=f"Failed to create log: {result.get('error')}")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exercise-logs/", response_model=List[ExerciseLogResponse], dependencies=[Depends(JWTBearer())])
async def get_exercise_logs(exercise_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("exercise_logs", token=token).eq("user_id", user_id).eq("exercise_id", exercise_id).execute()
        items = result.get("items", [])
        # Sort by logged_at desc, return last 5
        items_sorted = sorted(items, key=lambda x: x.get("logged_at", x.get("created", "")), reverse=True)
        return items_sorted[:20]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/exercise-logs/{log_id}/", dependencies=[Depends(JWTBearer())])
async def delete_exercise_log(log_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        result = pocketbase.table("exercise_logs", token=token).eq("id", log_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exercise-logs/pr/", response_model=PRResponse, dependencies=[Depends(JWTBearer())])
async def get_exercise_pr(exercise_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("exercise_logs", token=token).eq("user_id", user_id).eq("exercise_id", exercise_id).execute()
        items = result.get("items", [])
        if not items:
            return PRResponse(max_weight_kg=0, max_reps=0, best_volume=0, exercise_id=exercise_id)

        max_weight = max((float(i.get("weight_kg") or 0) for i in items), default=0)
        max_reps = max((int(i.get("reps") or 0) for i in items), default=0)
        best_volume = max(
            (float(i.get("sets") or 0) * float(i.get("reps") or 0) * float(i.get("weight_kg") or 0) for i in items),
            default=0
        )
        return PRResponse(max_weight_kg=max_weight, max_reps=max_reps, best_volume=best_volume, exercise_id=exercise_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exercise-logs/chart/", dependencies=[Depends(JWTBearer())])
async def get_exercise_chart(exercise_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("exercise_logs", token=token).eq("user_id", user_id).eq("exercise_id", exercise_id).execute()
        items = result.get("items", [])
        items_sorted = sorted(items, key=lambda x: x.get("logged_at", x.get("created", "")))
        return [
            {
                "id": i.get("id"),
                "weight_kg": float(i.get("weight_kg") or 0),
                "reps": int(i.get("reps") or 0),
                "sets": int(i.get("sets") or 0),
                "volume": float(i.get("sets") or 0) * float(i.get("reps") or 0) * float(i.get("weight_kg") or 0),
                "logged_at": i.get("logged_at") or i.get("created", ""),
            }
            for i in items_sorted
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── WORKOUT LOG ROUTES ────────────────────────────────────────────────────────

@router.post("/workout-logs/", response_model=WorkoutLogResponse, dependencies=[Depends(JWTBearer())])
async def create_workout_log(log: WorkoutLogCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        data = {
            "user_id": user_id,
            "folder_id": log.folder_id,
            "folder_name": log.folder_name,
            "logged_date": log.logged_date,
            "notes": log.notes or "",
        }
        result = pocketbase.table("workout_logs", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail=f"Failed to create workout log: {result.get('error')}")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workout-logs/", response_model=List[WorkoutLogResponse], dependencies=[Depends(JWTBearer())])
async def get_workout_logs(current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("workout_logs", token=token).eq("user_id", user_id).execute()
        return result.get("items", [])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/workout-logs/{log_id}/", dependencies=[Depends(JWTBearer())])
async def delete_workout_log(log_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        result = pocketbase.table("workout_logs", token=token).eq("id", log_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
