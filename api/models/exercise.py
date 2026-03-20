from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FolderCreate(BaseModel):
    name: str

class FolderResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created: str
    updated: str

    class Config:
        extra = "allow"

class SectionCreate(BaseModel):
    name: str
    description: Optional[str] = None

class SectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    section_id: Optional[str] = None
    folder_id: Optional[str] = None
    created: str
    updated: str

    class Config:
        extra = "allow"

class ExerciseCreate(BaseModel):
    section_id: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class ExerciseResponse(BaseModel):
    id: str
    section_id: str
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    image_url: Optional[str] = None
    collectionId: Optional[str] = None
    collectionName: Optional[str] = None
    target_sets: Optional[int] = 3
    target_reps: Optional[int] = 10
    created: str
    updated: str

    class Config:
        extra = "allow"
