# route.py
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from api.models.exercise import Exercise, Folder, Section, ExerciseUpdateRequest
from api.config.database import supabase
from typing import List
import traceback
from datetime import datetime
from fastapi import Form
import json
import uuid

router = APIRouter()

async def upload_to_supabase_storage(file: UploadFile, bucket_name: str = "exercise-images") -> str:
    """
    Upload a file to Supabase Storage and return the public URL
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate unique file name to avoid collisions
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Upload to Supabase Storage
        result = supabase.storage.from_(bucket_name).upload(
            unique_filename,
            file_content
        )
        
        # Get public URL
        file_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        
        return file_url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

async def delete_from_supabase_storage(file_path: str, bucket_name: str = "exercise-images") -> None:
    """
    Delete a file from Supabase Storage
    """
    try:
        # Extract filename from path
        filename = file_path.split('/')[-1]
        supabase.storage.from_(bucket_name).remove([filename])
    except Exception as e:
        print(f"Failed to delete file: {str(e)}")
        # Don't raise exception as this is cleanup operation

@router.post("/api/folders/{relative_folder_id}/sections/{section_id}/exercises")
async def create_exercise_in_section(
    relative_folder_id: str,
    section_id: str,
    exercise: str = Form(...),
    uploaded_image: UploadFile = File(...)
):
    try:
        exercise_data = json.loads(exercise)
        
        # Upload image to Supabase Storage
        image_url = await upload_to_supabase_storage(uploaded_image)
        
        exercise_dict = {
            "title": exercise_data["title"],
            "media_url": image_url,  # Store the public URL instead of base64 data
            "section_id": section_id,
            "folder_id": relative_folder_id,
            "description": exercise_data.get("description", "")
        }

        result = supabase.table('exercises').insert(exercise_dict).execute()
        
        return result.data[0]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exercise: {str(e)}"
        )

@router.put("/api/folders/{relative_folder_id}/sections/{section_id}/exercises/{exercise_id}")
async def update_exercise(
    relative_folder_id: str,
    section_id: str,
    exercise_id: str,
    exercise: str = Form(...),
    uploaded_image: UploadFile = File(None)
):
    try:
        # Get existing exercise
        existing_exercise = supabase.table('exercises').select("*").eq('id', exercise_id).execute()
        if not existing_exercise.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )

        exercise_data = json.loads(exercise)
        update_data = {
            "title": exercise_data.get("title"),
            "description": exercise_data.get("description")
        }

        # If new image is uploaded
        if uploaded_image:
            # Delete old image if exists
            old_media_url = existing_exercise.data[0].get('media_url')
            if old_media_url:
                await delete_from_supabase_storage(old_media_url)
            
            # Upload new image
            new_image_url = await upload_to_supabase_storage(uploaded_image)
            update_data["media_url"] = new_image_url

        # Update exercise in database
        result = supabase.table('exercises').update(update_data).eq('id', exercise_id).execute()

        return {
            "message": "Exercise updated successfully",
            "exercise": result.data[0]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update exercise: {str(e)}"
        )

@router.delete("/api/folders/{relative_folder_id}/sections/{section_id}/exercises/{exercise_id}")
async def delete_exercise(relative_folder_id: str, section_id: str, exercise_id: str):
    try:
        # Get exercise details first
        exercise = supabase.table('exercises').select("*").eq('id', exercise_id).execute()
        if not exercise.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )

        # Delete image from storage if exists
        media_url = exercise.data[0].get('media_url')
        if media_url:
            await delete_from_supabase_storage(media_url)

        # Delete exercise record
        result = supabase.table('exercises').delete().eq('id', exercise_id).execute()
        
        return {"message": "Exercise deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete exercise: {str(e)}"
        )