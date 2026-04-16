from fastapi import APIRouter, HTTPException, Depends
from ..config.database import pocketbase
from api.auth.auth_bearer import JWTBearer

router = APIRouter()


@router.get("/personal-records/", dependencies=[Depends(JWTBearer())])
async def get_all_prs(current_user: dict = Depends(JWTBearer())):
    """Return all personal records for the current user."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        result  = pocketbase.table("personal_records", token=token).eq("user_id", user_id).execute()
        items   = result.get("items", [])
        items.sort(key=lambda x: x.get("achieved_at", ""), reverse=True)
        return items
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/personal-records/{exercise_library_id}/", dependencies=[Depends(JWTBearer())])
async def get_exercise_pr(exercise_library_id: str, current_user: dict = Depends(JWTBearer())):
    """Return PR for a specific exercise (by exercise_library_id)."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")
        result  = pocketbase.table("personal_records", token=token)\
                            .eq("user_id", user_id)\
                            .eq("exercise_library_id", exercise_library_id).execute()
        items = result.get("items", [])
        if not items:
            return {
                "exercise_library_id": exercise_library_id,
                "max_weight_kg":       0,
                "max_reps":            0,
                "best_volume":         0,
                "best_1rm_estimate":   0,
                "achieved_at":         None,
            }
        return items[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/overview/", dependencies=[Depends(JWTBearer())])
async def get_stats_overview(current_user: dict = Depends(JWTBearer())):
    """Lifetime stats: total sessions, total volume, total PRs."""
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        sessions_result = pocketbase.table("workout_sessions", token=token).eq("user_id", user_id).execute()
        sessions = sessions_result.get("items", [])

        logs_result = pocketbase.table("exercise_logs", token=token).eq("user_id", user_id).execute()
        logs = logs_result.get("items", [])

        prs_result = pocketbase.table("personal_records", token=token).eq("user_id", user_id).execute()
        prs = prs_result.get("items", [])

        total_volume = sum(float(s.get("total_volume_kg") or 0) for s in sessions)
        if total_volume == 0:
            # Compute from logs if sessions don't have volume stored
            total_volume = sum(
                float(l.get("reps") or 0) * float(l.get("weight_kg") or 0)
                for l in logs
            )

        return {
            "total_sessions":  len(sessions),
            "total_volume_kg": round(total_volume, 2),
            "total_prs":       len(prs),
            "total_exercises_logged": len(set(
                l.get("exercise_library_id") or l.get("exercise_id", "")
                for l in logs if l.get("exercise_library_id") or l.get("exercise_id")
            )),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/weekly/", dependencies=[Depends(JWTBearer())])
async def get_weekly_stats(current_user: dict = Depends(JWTBearer())):
    """Weekly volume summary for the last 8 weeks."""
    import datetime
    try:
        token   = current_user.get("_token")
        user_id = current_user.get("id")

        sessions_result = pocketbase.table("workout_sessions", token=token).eq("user_id", user_id).execute()
        sessions = sessions_result.get("items", [])

        today   = datetime.date.today()
        weeks   = []
        for w in range(7, -1, -1):
            week_start = today - datetime.timedelta(days=today.weekday() + 7 * w)
            week_end   = week_start + datetime.timedelta(days=6)
            week_sessions = [
                s for s in sessions
                if week_start.isoformat() <= (s.get("session_date") or "") <= week_end.isoformat()
            ]
            week_volume = sum(float(s.get("total_volume_kg") or 0) for s in week_sessions)
            weeks.append({
                "week_start":    week_start.isoformat(),
                "week_label":    week_start.strftime("%b %d"),
                "session_count": len(week_sessions),
                "volume_kg":     round(week_volume, 2),
            })
        return weeks
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
