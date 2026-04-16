from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MuscleGroup(str, Enum):
    CHEST        = "chest"
    BACK         = "back"
    SHOULDERS    = "shoulders"
    BICEPS       = "biceps"
    TRICEPS      = "triceps"
    FOREARMS     = "forearms"
    QUADS        = "quads"
    HAMSTRINGS   = "hamstrings"
    GLUTES       = "glutes"
    CALVES       = "calves"
    CORE         = "core"
    FULL_BODY    = "full_body"
    CARDIO       = "cardio"


class Equipment(str, Enum):
    BARBELL          = "barbell"
    DUMBBELL         = "dumbbell"
    CABLE            = "cable"
    MACHINE          = "machine"
    BODYWEIGHT       = "bodyweight"
    KETTLEBELL       = "kettlebell"
    RESISTANCE_BAND  = "resistance_band"
    PULL_UP_BAR      = "pull_up_bar"
    OTHER            = "other"


class ExerciseCategory(str, Enum):
    STRENGTH    = "strength"
    CARDIO      = "cardio"
    FLEXIBILITY = "flexibility"


class ExerciseDifficulty(str, Enum):
    BEGINNER     = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED     = "advanced"


class ExerciseLibraryCreate(BaseModel):
    name:               str
    muscle_group:       MuscleGroup
    secondary_muscles:  Optional[str] = ""
    equipment:          Equipment
    category:           ExerciseCategory    = ExerciseCategory.STRENGTH
    difficulty:         ExerciseDifficulty  = ExerciseDifficulty.INTERMEDIATE
    description:        Optional[str] = ""
    instructions:       Optional[str] = ""


class ExerciseLibraryResponse(BaseModel):
    id:                 str
    name:               str
    muscle_group:       str
    secondary_muscles:  Optional[str] = ""
    equipment:          str
    category:           str
    difficulty:         str
    description:        Optional[str] = ""
    instructions:       Optional[str] = ""
    is_custom:          bool = False
    created_by:         Optional[str] = None

    class Config:
        extra = "allow"
