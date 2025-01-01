# exercise.py
from pydantic import BaseModel
from typing import Optional
from fastapi import UploadFile, File
from datetime import datetime

class Folder(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

class Section(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    folder_id: str
    created_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Section",
                "description": "Section description",
                "folder_id": "folder_id_here"
            }
        }

class Exercise(BaseModel):
    id: Optional[str] = None
    title: str
    media_url: str
    section_id: str
    folder_id: Optional[str] = None
    description: str
    upload_image: Optional[UploadFile] = None
    created_at: Optional[datetime] = None

class ExerciseUpdateRequest(BaseModel):
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    uploaded_image: Optional[UploadFile] = File(None)