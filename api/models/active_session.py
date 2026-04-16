from pydantic import BaseModel
from typing import Optional, List


class ActiveSessionCreate(BaseModel):
    template_id:    Optional[str] = None
    workout_name:   str


class ActiveSetCreate(BaseModel):
    exercise_library_id:    str
    exercise_name:          str
    set_number:             int
    reps:                   Optional[int]   = 0
    weight_kg:              Optional[float] = 0.0
    is_completed:           Optional[bool]  = False
    rest_seconds_after:     Optional[int]   = 90


class ActiveSetUpdate(BaseModel):
    reps:               Optional[int]   = None
    weight_kg:          Optional[float] = None
    is_completed:       Optional[bool]  = None


class ActiveSetResponse(BaseModel):
    id:                     str
    session_id:             str
    exercise_library_id:    str
    exercise_name:          str
    set_number:             int
    reps:                   Optional[int]   = 0
    weight_kg:              Optional[float] = 0.0
    is_completed:           bool = False
    rest_seconds_after:     Optional[int]   = 90
    logged_at:              Optional[str]   = ""
    created:                Optional[str]   = ""

    class Config:
        extra = "allow"


class ActiveSessionResponse(BaseModel):
    id:             str
    user_id:        str
    template_id:    Optional[str] = None
    workout_name:   str
    started_at:     str
    status:         str = "active"
    created:        Optional[str] = ""
    updated:        Optional[str] = ""

    class Config:
        extra = "allow"


class WorkoutFinishSummary(BaseModel):
    session_id:         str
    workout_name:       str
    duration_seconds:   int
    total_volume_kg:    float
    exercise_count:     int
    set_count:          int
    new_prs:            List[str] = []
    workout_session_id: Optional[str] = None
