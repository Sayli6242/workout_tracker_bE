from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class FolderCreate(BaseModel):
    name: str

class FolderResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

class SectionCreate(BaseModel):
    name: str
    description: Optional[str] = None

class SectionResponse(BaseModel):
    section_id: UUID
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime

class ExerciseCreate(BaseModel):
    section_id: UUID
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class ExerciseResponse(BaseModel):
    id: UUID
    section_id: UUID
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime