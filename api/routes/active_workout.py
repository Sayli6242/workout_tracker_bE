from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..config.database import pocketbase
from ..models.active_session import (
    ActiveSessionCreate, ActiveSessionResponse,
    ActiveSetCreate, ActiveSetUpdate, ActiveSetResponse,
    WorkoutFinishSummary
)
from api.auth.auth_bearer import JWTBearer
import datetime

router = APIRouter()


# ── ACTIVE WORKOUT ROUTES ─────────────────────────────────────────────────────

@router.get("/active-workout/current/", dependencies=[Depends(JWTBearer())])
async def get_current_session(current_user: dict = Depends(JWTBearer())):
    """Returns the in-progress session if one exists, else null."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        result  = pocketbase.table("active_workout_sessions", token=token)\
                             .eq("user_id", user_id).eq("status", "active").execute()
        items = result.get("items", [])
        if not items:
            return None
        session = items[0]

        sets_result = pocketbase.table("active_session_sets", token=token)\
                                .eq("session_id", session["id"]).execute()
        sets = sorted(sets_result.get("items", []), key=lambda x: (x.get("exercise_name",""), x.get("set_number", 0)))
        return {**session, "sets": sets}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/active-workout/", response_model=ActiveSessionResponse, dependencies=[Depends(JWTBearer())])
async def start_session(session: ActiveSessionCreate, current_user: dict = Depends(JWTBearer())):
    """Start a new active workout session (blank or from template)."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        # Discard any existing active session first
        existing = pocketbase.table("active_workout_sessions", token=token)\
                             .eq("user_id", user_id).eq("status", "active").execute()
        for old in existing.get("items", []):
            pocketbase.table("active_session_sets", token=token).eq("session_id", old["id"]).delete()
            pocketbase.table("active_workout_sessions", token=token).eq("id", old["id"]).delete()

        data = {
            "user_id":      user_id,
            "workout_name": session.workout_name,
            "started_at":   datetime.datetime.utcnow().isoformat() + "Z",
            "status":       "active",
        }
        if session.template_id:
            data["template_id"] = session.template_id
        result = pocketbase.table("active_workout_sessions", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to start session")

        new_session = result["items"][0]

        # If from template, pre-populate sets structure from template exercises
        if session.template_id:
            try:
                tex_result = pocketbase.table("template_exercises", token=token)\
                                       .eq("template_id", session.template_id).execute()
                template_exercises = sorted(tex_result.get("items", []), key=lambda x: x.get("order_index", 0))

                # Get last session data for pre-filling weights
                last_logs = _get_last_weights(token, user_id)

                for tex in template_exercises:
                    ex_id   = tex.get("exercise_library_id", "")
                    ex_name = tex.get("exercise_name", "")
                    last_weight = last_logs.get(ex_id, 0.0)
                    target_sets = int(tex.get("target_sets") or 3)
                    for s in range(1, target_sets + 1):
                        set_data = {
                            "session_id":          new_session["id"],
                            "exercise_library_id": ex_id,
                            "exercise_name":       ex_name,
                            "set_number":          s,
                            "reps":                int(tex.get("target_reps") or 10),
                            "weight_kg":           last_weight or float(tex.get("target_weight_kg") or 0),
                            "is_completed":        False,
                            "rest_seconds_after":  int(tex.get("rest_seconds") or 90),
                            "logged_at":           "",
                        }
                        pocketbase.table("active_session_sets", token=token).insert(set_data)
            except Exception:
                pass  # Pre-fill is best-effort

        return new_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _get_last_weights(token: str, user_id: str) -> dict:
    """Returns {exercise_library_id: last_weight_kg} from exercise_logs."""
    try:
        result = pocketbase.table("exercise_logs", token=token).eq("user_id", user_id).execute()
        items  = sorted(result.get("items", []), key=lambda x: x.get("logged_at", ""), reverse=True)
        seen   = {}
        for item in items:
            ex_id = item.get("exercise_library_id") or item.get("exercise_id", "")
            if ex_id and ex_id not in seen:
                seen[ex_id] = float(item.get("weight_kg") or 0)
        return seen
    except Exception:
        return {}


@router.get("/active-workout/{session_id}/", dependencies=[Depends(JWTBearer())])
async def get_session(session_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        s_result = pocketbase.table("active_workout_sessions", token=token)\
                             .eq("id", session_id).eq("user_id", user_id).execute()
        if not s_result.get("items"):
            raise HTTPException(status_code=404, detail="Session not found")
        session = s_result["items"][0]

        sets_result = pocketbase.table("active_session_sets", token=token)\
                                .eq("session_id", session_id).execute()
        sets = sorted(sets_result.get("items", []), key=lambda x: (x.get("exercise_name",""), x.get("set_number", 0)))
        return {**session, "sets": sets}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/active-workout/{session_id}/sets/",
             response_model=ActiveSetResponse, dependencies=[Depends(JWTBearer())])
async def add_set(session_id: str, set_data: ActiveSetCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        data  = {
            "session_id":          session_id,
            "exercise_library_id": set_data.exercise_library_id,
            "exercise_name":       set_data.exercise_name,
            "set_number":          set_data.set_number,
            "reps":                set_data.reps or 0,
            "weight_kg":           set_data.weight_kg or 0.0,
            "is_completed":        set_data.is_completed or False,
            "rest_seconds_after":  set_data.rest_seconds_after or 90,
            "logged_at":           datetime.datetime.utcnow().isoformat() + "Z" if set_data.is_completed else "",
        }
        result = pocketbase.table("active_session_sets", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to add set")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/active-workout/{session_id}/sets/{set_id}/",
            response_model=ActiveSetResponse, dependencies=[Depends(JWTBearer())])
async def update_set(
    session_id: str, set_id: str,
    set_data: ActiveSetUpdate,
    current_user: dict = Depends(JWTBearer())
):
    try:
        token = current_user.get("_token")
        data  = {"id": set_id}
        if set_data.reps is not None:         data["reps"] = set_data.reps
        if set_data.weight_kg is not None:    data["weight_kg"] = set_data.weight_kg
        if set_data.is_completed is not None:
            data["is_completed"] = set_data.is_completed
            if set_data.is_completed:
                data["logged_at"] = datetime.datetime.utcnow().isoformat() + "Z"

        result = pocketbase.table("active_session_sets", token=token).update(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to update set")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/active-workout/{session_id}/sets/{set_id}/", dependencies=[Depends(JWTBearer())])
async def delete_set(session_id: str, set_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        pocketbase.table("active_session_sets", token=token).eq("id", set_id).eq("session_id", session_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/active-workout/{session_id}/finish/",
             response_model=WorkoutFinishSummary, dependencies=[Depends(JWTBearer())])
async def finish_workout(session_id: str, current_user: dict = Depends(JWTBearer())):
    """
    Finalise the active workout:
    1. Save to workout_sessions
    2. Save completed sets to exercise_logs
    3. Detect and store new PRs
    4. Delete active session + sets
    """
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        # Get active session
        s_result = pocketbase.table("active_workout_sessions", token=token)\
                             .eq("id", session_id).eq("user_id", user_id).execute()
        if not s_result.get("items"):
            raise HTTPException(status_code=404, detail="Session not found")
        session = s_result["items"][0]

        # Get all sets
        sets_result = pocketbase.table("active_session_sets", token=token)\
                                .eq("session_id", session_id).execute()
        all_sets     = sets_result.get("items", [])
        completed    = [s for s in all_sets if s.get("is_completed")]

        # Calculate duration
        started_at = session.get("started_at", "")
        try:
            start_dt = datetime.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            duration = int((datetime.datetime.now(datetime.timezone.utc) - start_dt).total_seconds())
        except Exception:
            duration = 0

        # Compute totals
        total_volume = sum(
            float(s.get("reps") or 0) * float(s.get("weight_kg") or 0)
            for s in completed
        )
        unique_exercises = list({s.get("exercise_library_id") for s in completed if s.get("exercise_library_id")})

        # Save to workout_sessions
        session_data = {
            "user_id":        user_id,
            "workout_id":     session.get("template_id") or "quick",
            "workout_name":   session.get("workout_name", "Workout"),
            "workout_type":   "gym",
            "category":       "gym",
            "level":          "all",
            "tags":           "",
            "session_date":   datetime.date.today().isoformat(),
            "notes":          "",
            "duration_seconds": duration,
            "total_volume_kg":  round(total_volume, 2),
            "set_count":        len(completed),
            "exercise_count":   len(unique_exercises),
        }
        ws_result = pocketbase.table("workout_sessions", token=token).insert(session_data)
        workout_session_id = ws_result.get("items", [{}])[0].get("id") if ws_result.get("items") else None

        # Save exercise logs
        now_iso = datetime.datetime.utcnow().isoformat() + "Z"
        for s in completed:
            log_data = {
                "user_id":             user_id,
                "exercise_id":         s.get("exercise_library_id", ""),
                "exercise_library_id": s.get("exercise_library_id", ""),
                "exercise_name":       s.get("exercise_name", ""),
                "sets":                1,
                "reps":                int(s.get("reps") or 0),
                "weight_kg":           float(s.get("weight_kg") or 0),
                "notes":               "",
                "logged_at":           s.get("logged_at") or now_iso,
                "session_id":          workout_session_id or "",
                "is_pr":               False,
            }
            pocketbase.table("exercise_logs", token=token).insert(log_data)

        # Detect PRs per exercise
        new_prs = []
        for ex_id in unique_exercises:
            ex_sets = [s for s in completed if s.get("exercise_library_id") == ex_id]
            if not ex_sets:
                continue

            session_max_weight = max(float(s.get("weight_kg") or 0) for s in ex_sets)
            session_max_reps   = max(int(s.get("reps") or 0) for s in ex_sets)
            session_volume     = sum(float(s.get("reps") or 0) * float(s.get("weight_kg") or 0) for s in ex_sets)
            # Epley 1RM estimate
            best_set = max(ex_sets, key=lambda s: float(s.get("weight_kg") or 0))
            w = float(best_set.get("weight_kg") or 0)
            r = int(best_set.get("reps") or 0)
            one_rm = round(w * (1 + r / 30), 2) if r > 0 else w

            # Check existing PR
            pr_result = pocketbase.table("personal_records", token=token)\
                                  .eq("user_id", user_id).eq("exercise_library_id", ex_id).execute()
            pr_items  = pr_result.get("items", [])

            is_new_pr = False
            if pr_items:
                pr = pr_items[0]
                if (session_max_weight > float(pr.get("max_weight_kg") or 0) or
                    session_max_reps   > int(pr.get("max_reps") or 0) or
                    session_volume     > float(pr.get("best_volume") or 0)):
                    is_new_pr = True
                    pr_data = {
                        "id":                pr["id"],
                        "max_weight_kg":     max(session_max_weight, float(pr.get("max_weight_kg") or 0)),
                        "max_reps":          max(session_max_reps, int(pr.get("max_reps") or 0)),
                        "best_volume":       max(session_volume, float(pr.get("best_volume") or 0)),
                        "best_1rm_estimate": max(one_rm, float(pr.get("best_1rm_estimate") or 0)),
                        "achieved_at":       now_iso,
                    }
                    pocketbase.table("personal_records", token=token).update(pr_data)
            else:
                is_new_pr = True
                pr_data = {
                    "user_id":             user_id,
                    "exercise_library_id": ex_id,
                    "exercise_name":       ex_sets[0].get("exercise_name", ""),
                    "max_weight_kg":       session_max_weight,
                    "max_reps":            session_max_reps,
                    "best_volume":         session_volume,
                    "best_1rm_estimate":   one_rm,
                    "achieved_at":         now_iso,
                }
                pocketbase.table("personal_records", token=token).insert(pr_data)

            if is_new_pr:
                new_prs.append(ex_sets[0].get("exercise_name", ex_id))

        # Delete active session + sets
        pocketbase.table("active_session_sets", token=token).eq("session_id", session_id).delete()
        pocketbase.table("active_workout_sessions", token=token).eq("id", session_id).delete()

        # Update template last_used_at
        if session.get("template_id"):
            try:
                pocketbase.table("workout_templates", token=token).update({
                    "id": session["template_id"],
                    "last_used_at": now_iso,
                })
            except Exception:
                pass

        return WorkoutFinishSummary(
            session_id=session_id,
            workout_name=session.get("workout_name", "Workout"),
            duration_seconds=duration,
            total_volume_kg=round(total_volume, 2),
            exercise_count=len(unique_exercises),
            set_count=len(completed),
            new_prs=new_prs,
            workout_session_id=workout_session_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/active-workout/{session_id}/", dependencies=[Depends(JWTBearer())])
async def discard_session(session_id: str, current_user: dict = Depends(JWTBearer())):
    """Discard an active workout without saving."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        pocketbase.table("active_session_sets", token=token).eq("session_id", session_id).delete()
        pocketbase.table("active_workout_sessions", token=token)\
                  .eq("id", session_id).eq("user_id", user_id).delete()
        return {"discarded": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
