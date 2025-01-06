from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
from ..config.database import supabase
from ..models.exercise import (
    FolderCreate, FolderResponse,
    SectionCreate, SectionResponse,
    ExerciseCreate, ExerciseResponse
)
from api.auth.auth_bearer import JWTBearer
import magic
import uuid

router = APIRouter()

# Folder routes
@router.post("/folders/", response_model=FolderResponse, dependencies=[Depends(JWTBearer())])
async def create_folder(folder: FolderCreate, current_user: dict = Depends(JWTBearer())):
    try:
        if not current_user or not isinstance(current_user, dict):
            raise HTTPException(status_code=401, detail="Invalid user token")
            
        user_id = current_user.get("id")  # Using id instead of sub
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        data = {
            "name": folder.name,
            "user_id": user_id
        }
        print(f"Creating folder with data: {data}")  # Debug log
        result = supabase.table("folders").insert(data).execute()
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create folder")
        return result.data[0]
    except Exception as e:
        print(f"Error creating folder: {str(e)}")  # Debug log
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/folders/", response_model=List[FolderResponse], dependencies=[Depends(JWTBearer())])
async def get_folders(current_user: dict = Depends(JWTBearer())):
    try:
        user_id = current_user.get("id")
        result = supabase.table("folders").select("*").eq("user_id", user_id).execute()
        return result.data
    except Exception as e:
        print(f"Error getting folders: {str(e)}")  # Debug log

        raise HTTPException(status_code=400, detail=str(e))

@router.put("/folders/{id}/", response_model=FolderResponse, dependencies=[Depends(JWTBearer())])
async def update_folder(id: uuid.UUID, folder: FolderCreate, current_user: dict = Depends(JWTBearer())):
    try:
        user_id = current_user.get("id")
        data = {
            "name": folder.name
        }
        result = supabase.table("folders").update(data).eq("id", id).eq("user_id", user_id).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/folders/{id}/", response_model=bool, dependencies=[Depends(JWTBearer())])
async def delete_folder(id: uuid.UUID, current_user: dict = Depends(JWTBearer())):
    try:
        user_id = current_user.get("id")
        result = supabase.table("folders").delete().eq("id", id).eq("user_id", user_id).execute()
        return len(result.data) > 0
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# Section routes
@router.post("/folders/{folder_id}/sections/", response_model=SectionResponse, dependencies=[Depends(JWTBearer())])
async def create_section(folder_id:uuid.UUID , section: SectionCreate, current_user:dict = Depends(JWTBearer())):
    try:
        user_id = current_user.get("id")
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.data:
            raise HTTPException(status_code=404, detail="Folder not found")
        section_data = {
            "name" : section.name,
            "description" : section.description,
            "folder_id" : str(folder_id)
        }
        result = supabase.table("sections").insert(section_data).execute()
        return result.data[0]
    except Exception as e:
        print("Error creating section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/folders/{folder_id}/sections/", response_model=List[SectionResponse], dependencies=[Depends(JWTBearer())])
async def get_sections(folder_id: uuid.UUID):
    try:
        result = supabase.table("sections").select("*").eq("folder_id", str(folder_id)).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Exercise routes
@router.post("/exercises/", response_model=ExerciseResponse, dependencies=[Depends(JWTBearer())])
async def create_exercise(exercise: ExerciseCreate):
    try:
        result = supabase.table("exercises").insert(exercise.dict()).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sections/{section_id}/exercises/", response_model=List[ExerciseResponse], dependencies=[Depends(JWTBearer())])
async def get_exercises(section_id: uuid.UUID):
    try:
        result = supabase.table("exercises").select("*").eq("section_id", str(section_id)).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Image upload route
@router.post("/upload-image/", dependencies=[Depends(JWTBearer())])
async def upload_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_ext = file.filename.split('.')[-1].lower()
        
        # Basic file type check
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="File must be an image")
        
        file_path = f"exercises/{uuid.uuid4()}.{file_ext}"
        
        # Upload to Supabase Storage
        result = supabase.storage.from_("exercises").upload(
            file_path,
            content
        )
        
        # Get public URL
        public_url = supabase.storage.from_("exercises").get_public_url(file_path)
        
        return {"image_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))