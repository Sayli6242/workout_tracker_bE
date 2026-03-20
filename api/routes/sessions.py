from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
from ..config.database import pocketbase
from api.auth.auth_bearer import JWTBearer
import datetime

router = APIRouter()


# ── WORKOUT TYPES ─────────────────────────────────────────────────────────────

class WorkoutType(str, Enum):
    # HIIT / Cardio
    HIIT                = "hiit"
    # Gym / Equipment
    GYM                 = "gym"
    MACHINE             = "machine"
    EQUIPMENT           = "equipment"
    # Skill-level general
    BEGINNER            = "beginner"
    INTERMEDIATE        = "intermediate"
    PRO                 = "pro"
    # Yoga
    YOGA                = "yoga"
    MAT_YOGA            = "mat_yoga"
    BEGINNER_YOGA       = "beginner_yoga"
    INTERMEDIATE_YOGA   = "intermediate_yoga"
    MORNING_YOGA        = "morning_yoga"
    RELAXATION_YOGA     = "relaxation_yoga"
    STRESS_RELIEF_YOGA  = "stress_relief_yoga"


# Metadata: label, category, level, searchable tags
WORKOUT_TYPE_META: dict = {
    WorkoutType.HIIT: {
        "label":    "HIIT",
        "category": "cardio",
        "level":    "intermediate",
        "tags":     ["hiit", "cardio", "high-intensity", "fat-burn", "interval"],
    },
    WorkoutType.GYM: {
        "label":    "Gym Workout",
        "category": "gym",
        "level":    "all",
        "tags":     ["gym", "weights", "strength", "resistance"],
    },
    WorkoutType.MACHINE: {
        "label":    "Machine Workout",
        "category": "gym",
        "level":    "all",
        "tags":     ["machine", "gym", "equipment", "isolation", "cable"],
    },
    WorkoutType.EQUIPMENT: {
        "label":    "Equipment Workout",
        "category": "gym",
        "level":    "all",
        "tags":     ["equipment", "dumbbells", "barbells", "free-weights", "kettlebell"],
    },
    WorkoutType.BEGINNER: {
        "label":    "Beginner Level",
        "category": "general",
        "level":    "beginner",
        "tags":     ["beginner", "starter", "easy", "no-equipment", "bodyweight"],
    },
    WorkoutType.INTERMEDIATE: {
        "label":    "Intermediate Level",
        "category": "general",
        "level":    "intermediate",
        "tags":     ["intermediate", "moderate", "progression"],
    },
    WorkoutType.PRO: {
        "label":    "Pro / Advanced",
        "category": "general",
        "level":    "advanced",
        "tags":     ["pro", "advanced", "intense", "high-performance", "athlete"],
    },
    WorkoutType.YOGA: {
        "label":    "Yoga",
        "category": "yoga",
        "level":    "all",
        "tags":     ["yoga", "flexibility", "mindfulness", "balance", "stretch"],
    },
    WorkoutType.MAT_YOGA: {
        "label":    "Mat Yoga",
        "category": "yoga",
        "level":    "all",
        "tags":     ["mat-yoga", "yoga", "floor", "flexibility", "core"],
    },
    WorkoutType.BEGINNER_YOGA: {
        "label":    "Beginner Yoga",
        "category": "yoga",
        "level":    "beginner",
        "tags":     ["beginner-yoga", "yoga", "starter", "easy", "gentle"],
    },
    WorkoutType.INTERMEDIATE_YOGA: {
        "label":    "Intermediate Yoga",
        "category": "yoga",
        "level":    "intermediate",
        "tags":     ["intermediate-yoga", "yoga", "balance", "strength"],
    },
    WorkoutType.MORNING_YOGA: {
        "label":    "Morning Yoga",
        "category": "yoga",
        "level":    "all",
        "tags":     ["morning-yoga", "yoga", "energizing", "wake-up", "sunrise"],
    },
    WorkoutType.RELAXATION_YOGA: {
        "label":    "Relaxation Yoga",
        "category": "yoga",
        "level":    "all",
        "tags":     ["relaxation", "yoga", "calm", "restore", "yin", "restorative"],
    },
    WorkoutType.STRESS_RELIEF_YOGA: {
        "label":    "Stress Relief Yoga",
        "category": "yoga",
        "level":    "all",
        "tags":     ["stress-relief", "yoga", "mindfulness", "anxiety", "calm", "breathwork"],
    },
}


# ── SCHEMAS ───────────────────────────────────────────────────────────────────

class WorkoutSessionCreate(BaseModel):
    workout_id:   str
    workout_name: str
    workout_type: Optional[WorkoutType] = None
    session_date: Optional[str] = ""
    notes:        Optional[str] = ""


class WorkoutSessionResponse(BaseModel):
    id:           str
    user_id:      str
    workout_id:   str
    workout_name: str
    workout_type: Optional[str]  = None
    category:     Optional[str]  = None
    level:        Optional[str]  = None
    tags:         Optional[List[str]] = []
    session_date: str
    notes:        Optional[str]  = ""
    created:      Optional[str]  = ""
    updated:      Optional[str]  = ""

    class Config:
        extra = "allow"


class WorkoutTypeInfo(BaseModel):
    type:     str
    label:    str
    category: str
    level:    str
    tags:     List[str]


# ── WORKOUT TYPES LISTING ─────────────────────────────────────────────────────

@router.get("/workout-types/", response_model=List[WorkoutTypeInfo])
async def list_workout_types(
    category: Optional[str] = Query(None, description="Filter by category: cardio, gym, general, yoga"),
    level:    Optional[str] = Query(None, description="Filter by level: beginner, intermediate, advanced, all"),
    tag:      Optional[str] = Query(None, description="Filter by tag keyword"),
):
    """Return all available workout types with their tags. Supports filter by category, level, or tag."""
    result = []
    for wtype, meta in WORKOUT_TYPE_META.items():
        if category and meta["category"] != category:
            continue
        if level and meta["level"] not in (level, "all"):
            continue
        if tag and tag.lower() not in [t.lower() for t in meta["tags"]]:
            continue
        result.append(WorkoutTypeInfo(
            type=wtype.value,
            label=meta["label"],
            category=meta["category"],
            level=meta["level"],
            tags=meta["tags"],
        ))
    return result


# ── SESSION ROUTES ────────────────────────────────────────────────────────────

@router.post("/workout-sessions/", response_model=WorkoutSessionResponse, dependencies=[Depends(JWTBearer())])
async def create_session(session: WorkoutSessionCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        date    = session.session_date or datetime.date.today().isoformat()

        meta     = WORKOUT_TYPE_META.get(session.workout_type, {}) if session.workout_type else {}
        category = meta.get("category", "")
        level    = meta.get("level", "")
        tags     = meta.get("tags", [])

        data = {
            "user_id":      user_id,
            "workout_id":   session.workout_id,
            "workout_name": session.workout_name,
            "workout_type": session.workout_type.value if session.workout_type else "",
            "category":     category,
            "level":        level,
            "tags":         ",".join(tags),          # stored as comma-separated string
            "session_date": date,
            "notes":        session.notes or "",
        }
        result = pocketbase.table("workout_sessions", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to create session")

        item = result["items"][0]
        # Deserialize tags back to list for the response
        item["tags"] = [t for t in item.get("tags", "").split(",") if t]
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workout-sessions/", response_model=List[WorkoutSessionResponse], dependencies=[Depends(JWTBearer())])
async def get_sessions(
    current_user:  dict = Depends(JWTBearer()),
    workout_type:  Optional[WorkoutType] = Query(None, description="Filter by workout type"),
    category:      Optional[str]         = Query(None, description="Filter by category"),
    level:         Optional[str]         = Query(None, description="Filter by level"),
    tag:           Optional[str]         = Query(None, description="Filter by tag keyword"),
    sort_by:       Optional[str]         = Query("session_date", description="Sort field: session_date, workout_type, workout_name"),
    sort_order:    Optional[str]         = Query("desc", description="Sort order: asc or desc"),
):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        result  = pocketbase.table("workout_sessions", token=token).eq("user_id", user_id).execute()
        items   = result.get("items", [])

        # Deserialize tags string → list
        for item in items:
            raw_tags = item.get("tags", "")
            item["tags"] = [t for t in raw_tags.split(",") if t] if isinstance(raw_tags, str) else (raw_tags or [])

        # ── Filters ──
        if workout_type:
            items = [i for i in items if i.get("workout_type") == workout_type.value]
        if category:
            items = [i for i in items if i.get("category") == category]
        if level:
            items = [i for i in items if i.get("level") == level]
        if tag:
            items = [i for i in items if tag.lower() in [t.lower() for t in i.get("tags", [])]]

        # ── Sort ──
        reverse = sort_order.lower() != "asc"
        valid_sort_fields = {"session_date", "workout_type", "workout_name", "created"}
        field = sort_by if sort_by in valid_sort_fields else "session_date"
        items.sort(key=lambda x: x.get(field, ""), reverse=reverse)

        return items
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workout-sessions/{session_id}/", dependencies=[Depends(JWTBearer())])
async def get_session(session_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        s_result = pocketbase.table("workout_sessions", token=token).eq("id", session_id).eq("user_id", user_id).execute()
        if not s_result.get("items"):
            raise HTTPException(status_code=404, detail="Session not found")
        session = s_result["items"][0]
        raw_tags = session.get("tags", "")
        session["tags"] = [t for t in raw_tags.split(",") if t] if isinstance(raw_tags, str) else (raw_tags or [])

        logs_result = pocketbase.table("exercise_logs", token=token).eq("session_id", session_id).execute()
        return {**session, "exercise_logs": logs_result.get("items", [])}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/workout-sessions/{session_id}/", dependencies=[Depends(JWTBearer())])
async def delete_session(session_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        pocketbase.table("workout_sessions", token=token).eq("id", session_id).eq("user_id", user_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
