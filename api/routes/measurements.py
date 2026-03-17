from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..config.database import pocketbase
from ..models.logs import MeasurementCreate, MeasurementResponse
from api.auth.auth_bearer import JWTBearer
import datetime

router = APIRouter()


@router.post("/measurements/", response_model=MeasurementResponse, dependencies=[Depends(JWTBearer())])
async def create_measurement(measurement: MeasurementCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        data = {
            "user_id": user_id,
            "weight_kg": measurement.weight_kg,
            "body_fat_pct": measurement.body_fat_pct,
            "chest_cm": measurement.chest_cm,
            "waist_cm": measurement.waist_cm,
            "hips_cm": measurement.hips_cm,
            "arms_cm": measurement.arms_cm,
            "legs_cm": measurement.legs_cm,
            "logged_at": measurement.logged_at or datetime.datetime.utcnow().isoformat() + "Z",
        }
        result = pocketbase.table("measurements", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail=f"Failed to create measurement: {result.get('error')}")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/measurements/", response_model=List[MeasurementResponse], dependencies=[Depends(JWTBearer())])
async def get_measurements(current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("measurements", token=token).eq("user_id", user_id).execute()
        items = result.get("items", [])
        items_sorted = sorted(items, key=lambda x: x.get("logged_at", x.get("created", "")), reverse=True)
        return items_sorted
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/measurements/{measurement_id}/", dependencies=[Depends(JWTBearer())])
async def delete_measurement(measurement_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        result = pocketbase.table("measurements", token=token).eq("id", measurement_id).delete()
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
