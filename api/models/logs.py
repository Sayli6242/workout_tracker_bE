from pydantic import BaseModel
from typing import Optional


class ExerciseLogCreate(BaseModel):
    exercise_id: str
    sets: int
    reps: int
    weight_kg: float
    notes: Optional[str] = ""
    logged_at: Optional[str] = ""
    session_id: Optional[str] = ""


class ExerciseLogResponse(BaseModel):
    id: str
    user_id: str
    exercise_id: str
    sets: int
    reps: int
    weight_kg: float
    notes: Optional[str] = ""
    logged_at: Optional[str] = ""
    session_id: Optional[str] = ""
    created: Optional[str] = ""
    updated: Optional[str] = ""

    class Config:
        extra = "allow"


class WorkoutLogCreate(BaseModel):
    folder_id: str
    folder_name: str
    logged_date: str
    notes: Optional[str] = ""


class WorkoutLogResponse(BaseModel):
    id: str
    user_id: str
    folder_id: str
    folder_name: str
    logged_date: str
    notes: Optional[str] = ""
    created: Optional[str] = ""
    updated: Optional[str] = ""

    class Config:
        extra = "allow"


class PRResponse(BaseModel):
    max_weight_kg: float
    max_reps: int
    best_volume: float
    exercise_id: str


class MeasurementCreate(BaseModel):
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    arms_cm: Optional[float] = None
    legs_cm: Optional[float] = None
    logged_at: Optional[str] = ""


class MeasurementResponse(BaseModel):
    id: str
    user_id: str
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    arms_cm: Optional[float] = None
    legs_cm: Optional[float] = None
    logged_at: Optional[str] = ""
    created: Optional[str] = ""
    updated: Optional[str] = ""

    class Config:
        extra = "allow"
