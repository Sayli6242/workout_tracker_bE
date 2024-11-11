# exercise.py
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from fastapi import UploadFile, File
class Folder(BaseModel):
    name: str  # Required field
    # parent_id: Optional[str] = None  # Optional parent folder ID, defaults to None for root folders
    description: Optional[str] = None  # Optional description field
    id: Optional[str] = None  # Make id optional

   
    class Config:
        # This allows the model to work with MongoDB's ObjectId
        json_encoders = {
            ObjectId: str
        }

class Section(BaseModel):
    
    name: str
    description: Optional[str] = None
    id: Optional[str] = None
    folder_id: str # Required field - references the parent folder
    
    
    
    class Config:
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "My Section",
                 "description": "Section description",
                "folder_id": "folder_id_here"
            }
        }

class Exercise(BaseModel):
    id: Optional[str] = None
    title: str  # Required field
    media_url: str  # Required field
    section_id: str  # Required field - references the parent section
    folder_id: Optional[str] = None
    description: str
    upload_image: Optional[UploadFile] = None


class ExerciseUpdateRequest(BaseModel):
    id : str 
    title: str = None
    description: str = None
    uploaded_image: UploadFile = File(None)


    class Config:
        json_encoders = {
            ObjectId: str
        }
        