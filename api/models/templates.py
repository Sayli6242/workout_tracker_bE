from pydantic import BaseModel
from typing import Optional


class TemplateCreate(BaseModel):
    name:                   str
    workout_type:           Optional[str] = ""
    estimated_duration_min: Optional[int] = 45
    difficulty:             Optional[str] = "intermediate"
    description:            Optional[str] = ""


class TemplateUpdate(BaseModel):
    name:                   Optional[str] = None
    workout_type:           Optional[str] = None
    estimated_duration_min: Optional[int] = None
    difficulty:             Optional[str] = None
    description:            Optional[str] = None


class TemplateResponse(BaseModel):
    id:                     str
    user_id:                str
    name:                   str
    workout_type:           Optional[str] = ""
    estimated_duration_min: Optional[int] = 45
    difficulty:             Optional[str] = "intermediate"
    description:            Optional[str] = ""
    last_used_at:           Optional[str] = ""
    created:                Optional[str] = ""
    updated:                Optional[str] = ""

    class Config:
        extra = "allow"


class TemplateExerciseCreate(BaseModel):
    exercise_library_id:    str
    exercise_name:          str
    order_index:            int
    target_sets:            Optional[int]   = 3
    target_reps:            Optional[int]   = 10
    target_weight_kg:       Optional[float] = 0.0
    rest_seconds:           Optional[int]   = 90


class TemplateExerciseResponse(BaseModel):
    id:                     str
    template_id:            str
    exercise_library_id:    str
    exercise_name:          str
    order_index:            int
    target_sets:            Optional[int]   = 3
    target_reps:            Optional[int]   = 10
    target_weight_kg:       Optional[float] = 0.0
    rest_seconds:           Optional[int]   = 90
    created:                Optional[str]   = ""

    class Config:
        extra = "allow"
