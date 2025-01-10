from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
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
import datetime
import pytz
from fastapi import Path





router = APIRouter()

@router.get("/folders/{folder_id}", response_model=FolderResponse, dependencies=[Depends(JWTBearer())])
async def get_folder(folder_id: uuid.UUID, current_user: dict = Depends(JWTBearer())):
    try:
        user_id = current_user.get("id")
        result = supabase.table("folders").select("*").eq("id", str(folder_id)).eq("user_id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Folder not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    



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



@router.get("/folders/{folder_id}/sections/{section_id}/", response_model=SectionResponse, dependencies=[Depends(JWTBearer())])
async def get_section(
    folder_id: uuid.UUID,
    section_id: uuid.UUID,
    current_user: dict = Depends(JWTBearer())
):
    try:
        # Verify the folder belongs to the user
        user_id = current_user.get("id")
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.data:
            raise HTTPException(status_code=404, detail="Folder not found")
            
        # Get section data
        result = supabase.table("sections")\
            .select("*")\
            .eq("section_id", str(section_id))\
            .eq("id", str(folder_id))\
            .execute()
            
        if not result.data:
            raise HTTPException(status_code=404, detail="Section not found")
            
        return result.data[0]
    except Exception as e:
        print("Error getting section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
    
    
# Section routes
@router.post("/folders/{folder_id}/sections/", response_model=SectionResponse, dependencies=[Depends(JWTBearer())])
async def create_section(folder_id:uuid.UUID , section: SectionCreate, current_user:dict = Depends(JWTBearer())):
    try:
        user_id = current_user.get("id")
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.data:
            raise HTTPException(status_code=404, detail="Folder not found")
        if not folder.data[0]:  # Check if the folder is empty
            raise HTTPException(status_code=400, detail="Folder is empty")
        
        section_data = {
            "section_id": str(uuid.uuid4()),
            "name" : section.name,
            "description" : section.description,
            "id" : str(folder_id),  # Note: id represents the folder_id
            "created_at": datetime.datetime.now(tz=pytz.utc).isoformat()
}
  # Modify these lines to handle the response correctly
        result = supabase.table("sections").insert(section_data).execute()

         # Check if result is not None and has data
        if result and hasattr(result, 'data') and result.data:
            return result.data[0]
    except Exception as e:
        print("Error creating section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/folders/{folder_id}/sections/", response_model=List[SectionResponse], dependencies=[Depends(JWTBearer())])
async def get_sections(folder_id: uuid.UUID, current_user: dict = Depends(JWTBearer())):
    try:
        # First verify the folder belongs to the user
        user_id = current_user.get("id")
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.data:
            raise HTTPException(status_code=404, detail="Folder not found")
            
        # Get sections for the folder
        result = supabase.table("sections").select("*").eq("id", str(folder_id)).execute()
        return result.data
    except Exception as e:
        print("Error getting sections:", str(e))
        raise HTTPException(status_code=400, detail=str(e))



@router.put("/folders/{folder_id}/sections/{section_id}", response_model=SectionResponse, dependencies=[Depends(JWTBearer())])
async def update_section(
    folder_id: uuid.UUID,
    section_id: uuid.UUID,
    section: SectionCreate,
    current_user: dict = Depends(JWTBearer())
):
    try:
        # Verify the folder belongs to the user
        user_id = current_user.get("id")
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.data:
            raise HTTPException(status_code=404, detail="Folder not found")
            
        # Update section data
        section_data = {
            "name": section.name,
            "description": section.description
        }
        
        result = supabase.table("sections")\
            .update(section_data)\
            .eq("section_id", str(section_id))\
            .eq("id", str(folder_id))\
            .execute()
            
        if not result.data:
            raise HTTPException(status_code=404, detail="Section not found")
            
        return result.data[0]
    except Exception as e:
        print("Error updating section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))




@router.delete("/folders/{folder_id}/sections/{section_id}", dependencies=[Depends(JWTBearer())])
async def delete_section(
    folder_id: uuid.UUID,
    section_id: uuid.UUID,
    current_user: dict = Depends(JWTBearer())
):
    try:
        # Verify the folder belongs to the user
        user_id = current_user.get("id")
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.data:
            raise HTTPException(status_code=404, detail="Folder not found")
            
        # Delete the section
        result = supabase.table("sections")\
            .delete()\
            .eq("section_id", str(section_id))\
            .eq("id", str(folder_id))\
            .execute()
            
        if not result.data:
            raise HTTPException(status_code=404, detail="Section not found")
            
        return {"message": "Section deleted successfully"}
    except Exception as e:
        print("Error deleting section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))






@router.get("/folders/{folder_id}/sections/{section_id}/exercises/", response_model=List[ExerciseResponse], dependencies=[Depends(JWTBearer())])
async def get_exercise(
    folder_id: uuid.UUID = Path(...),
    section_id: uuid.UUID = Path(...),
    current_user: dict = Depends(JWTBearer())
):
    try:
        # Verify user has access to the folder
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.data:
            raise HTTPException(status_code=404, detail="Folder not found or unauthorized")
            
        # Get exercises for the section
        result = supabase.table("exercises").select("*").eq("section_id", str(section_id)).execute()
        return result.data
    except Exception as e:
        print(f"Error getting exercises: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))









@router.post("/folders/{folder_id}/sections/{section_id}/exercises/", response_model=ExerciseResponse)
async def create_exercise(
    folder_id: uuid.UUID = Path(...),
    section_id: uuid.UUID = Path(...),
    name: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    current_user: dict = Depends(JWTBearer())
):
    try:
        if not current_user or not isinstance(current_user, dict):
            raise HTTPException(status_code=401, detail="Invalid user token")
            
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Verify section exists
        section = supabase.table("sections").select("*").eq("section_id", str(section_id)).execute()
        if not section.data:
            raise HTTPException(status_code=404, detail="Section not found or unauthorized")

        # Handle image upload if provided
        image_url = None
        if image:
            try:
                content = await image.read()
                file_ext = image.filename.split('.')[-1].lower()
                
                # Generate unique filename
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                file_path = f"exercises/{unique_filename}"
                
                # Upload to Supabase Storage - modified to handle response correctly
                storage_response = supabase.storage.from_("exercises").upload(
                    path=file_path,
                    file=content,
                )
                
                # Get public URL only if upload was successful
                if storage_response:
                    image_url = supabase.storage.from_("exercises").get_public_url(file_path)
                else:
                    raise HTTPException(status_code=400, detail="Failed to upload image")
                    
            except Exception as e:
                print(f"Error uploading image: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error uploading image: {str(e)}")

        # Create exercise data
        exercise_data = {
            "section_id": str(section_id),
            "name": name,
            "description": description if description else "",
            "image_url": image_url
        }
        
        # Insert exercise into database
        result = supabase.table("exercises").insert(exercise_data).execute()
        
        if not result.data:
            # Clean up uploaded image if exercise creation fails
            if image_url:
                try:
                    supabase.storage.from_("exercises").remove([file_path])
                except:
                    pass
            raise HTTPException(status_code=400, detail="Failed to create exercise")
            
        return result.data[0]
    except Exception as e:
        print(f"Error creating exercise: {str(e)}")
        # If it's already an HTTPException, re-raise it
        if isinstance(e, HTTPException):
            raise e
        # Otherwise, wrap it in an HTTPException
        raise HTTPException(status_code=400, detail=str(e))



@router.delete("/folders/{folder_id}/sections/{section_id}/exercises/{exercise_id}/", dependencies=[Depends(JWTBearer())])
async def delete_exercise(
    folder_id: uuid.UUID = Path(...),
    section_id: uuid.UUID = Path(...),
    exercise_id: uuid.UUID = Path(...),
    current_user: dict = Depends(JWTBearer())
):
    try:
        # Verify user has access to the folder
        user_id = current_user.get("id")
        folder = supabase.table("folders").select("*").eq("id", folder_id).eq("user_id", user_id).execute()
        
        if not folder.data:
            raise HTTPException(status_code=403, detail="Not authorized to access this folder")

        # Verify the section exists in the folder
        section = supabase.table("sections").select("*").eq("section_id", str(section_id)).eq("id", str(folder_id)).execute()
        
        if not section.data:
            raise HTTPException(status_code=404, detail="Section not found")

        # Delete the exercise
        exercise = supabase.table("exercises").select("*").eq("id", str(exercise_id)).eq("section_id", str(section_id)).execute()
        
        if not exercise.data:
            raise HTTPException(status_code=404, detail="Exercise not found")

        # Delete image if it exists
        if exercise.data[0].get("image_url"):
            try:
                file_path = exercise.data[0]["image_url"].split("/")[-1]
                supabase.storage.from_("exercises").remove([f"exercises/{file_path}"])
            except Exception as e:
                print(f"Error deleting image: {str(e)}")

        result = supabase.table("exercises").delete().eq("id", str(exercise_id)).execute()
        return {"message": "Exercise deleted successfully"}

    except Exception as e:
        print(f"Error deleting exercise: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/folders/{folder_id}/sections/{section_id}/exercises/{exercise_id}/", response_model=ExerciseResponse, dependencies=[Depends(JWTBearer())])
async def update_exercise(
    folder_id: uuid.UUID = Path(...),
    section_id: uuid.UUID = Path(...),
    exercise_id: uuid.UUID = Path(...),
    name: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    current_user: dict = Depends(JWTBearer())
):
    try:
        # Verify user has access to the folder
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
            
        # Verify folder ownership
        folder = supabase.table("folders").select("*").eq("id", str(folder_id)).eq("user_id", str(user_id)).execute()
        if not folder.data:
            raise HTTPException(status_code=403, detail="Folder not found or unauthorized")
            
        # Get existing exercise
        existing_exercise = supabase.table("exercises").select("*").eq("id", str(exercise_id)).single().execute()
        if not existing_exercise.data:
            raise HTTPException(status_code=404, detail="Exercise not found")

        # Handle image update if provided
        image_url = existing_exercise.data.get("image_url")  # Keep existing image URL by default
        if image:
            # Delete existing image if there is one
            if image_url:
                try:
                    old_file_path = image_url.split("/")[-1]
                    supabase.storage.from_("exercises").remove([f"exercises/{old_file_path}"])
                except Exception as e:
                    print(f"Error deleting old image: {str(e)}")

            # Upload new image
            content = await image.read()
            file_ext = image.filename.split('.')[-1].lower()
            
            # Generate unique filename
            file_path = f"exercises/{uuid.uuid4()}.{file_ext}"
            
            # Upload to Supabase Storage
            try:
                upload_result = supabase.storage.from_("exercises").upload(
                    file_path,
                    content
                )
                
                # Get public URL
                image_url = supabase.storage.from_("exercises").get_public_url(file_path)
            except Exception as e:
                print(f"Error uploading image: {str(e)}")
                raise HTTPException(status_code=400, detail="Failed to upload image")

        # Update exercise data
        exercise_data = {
            "name": name,
            "description": description,
            "image_url": image_url
        }
        
        result = supabase.table("exercises").update(exercise_data).eq("id", str(exercise_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update exercise")
            
        return result.data[0]
    except Exception as e:
        print(f"Error updating exercise: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
