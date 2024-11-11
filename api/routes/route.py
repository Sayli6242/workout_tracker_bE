# route.py
from fastapi import APIRouter, HTTPException, status, UploadFile, File 
from models.exercise import Exercise, Folder, Section, ExerciseUpdateRequest
from config.database import db
from typing import List
from bson import ObjectId
from bson.errors import InvalidId
from bson.binary import Binary
import traceback
from datetime import datetime
from fastapi import Form
import json
from fastapi.responses import Response
import base64

router = APIRouter()

# Helper functions
def prepare_document(document):
# Convert ObjectId to string
    return {
        "id": str(document.get("_id", None)),
        "name": document.get("name", None),
        "description": document.get("description", None),
        "folder_id": document.get("folder_id", None),
        "section_id": str(document.get("_id"))
        
    }

def prepare_exercise(doc):
    
    return {
        "id": str(doc.get("_id", None)),
        "title" : doc.get("title",""),
        "media_url" : doc.get("media_url",""),
        "section_id" : str(doc.get("section_id")),
        "folder_id" : doc.get("folder_id",""),
        "description": doc.get("description", "")
        }

def validate_folder_name(folder_dict):
    if not folder_dict.get("name"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder name is required"
        )
        
# Update the create_folder route
@router.post("/api/folders", response_model=Folder)
async def create_folder(folder: Folder):
    try:
        folder_dict = folder.dict(exclude_unset=True)
        validate_folder_name(folder_dict)
        result = await db.folders.insert_one(folder_dict)
        return {**folder_dict, "id": str(result.inserted_id)}
    except Exception as e:
        print(f"Error creating folder: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create folder: {str(e)}"
        )
@router.get("/api/folders/", response_model=List[Folder])
async def get_folders():
    try:
        folders = []
        cursor = db.folders.find({}, {"name": 1, "_id": 1})
        async for document in cursor:
            folders.append(prepare_document(document))
        return folders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve folders: {str(e)}"
        )

@router.get("/api/folders/{id}", response_model=List[Folder])
async def get_folder_details(id : str):
    try:
    
        folder = await db.folders.find_one({"_id": ObjectId(id)}, {"name": 1, "_id": 1})
        if folder:
            return [prepare_document(folder)]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve folders: {str(e)}"
        )


# Add new update_folder route
@router.put("/api/folders/{id}")
async def update_folder(id: str, folder: Folder):
    try:
        folder_dict = folder.dict(exclude_unset=True)
        validate_folder_name(folder_dict)
        
        # Remove id if present in the update data
        if "id" in folder_dict:
            del folder_dict["id"]
            
        result = await db.folders.update_one(
            {"_id": ObjectId(id)},
            {"$set": folder_dict}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
            
        return {"message": "Folder updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update folder: {str(e)}"
        )

@router.delete("/api/folders/{id}")
async def delete_folder(id: str):
    try:
        await db.folders.delete_one({"_id": ObjectId(id)})
        return {"message": "Folder deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete folder: {str(e)}"
        )



@router.post("/api/folders/{id}/section", response_model=Section)
async def create_section(id: str, section: Section):
    try:
        folder = await db.folders.find_one({"_id": ObjectId(id)})
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
        
        section_dict = section.dict(exclude_unset=True)
        result = await db.sections.insert_one(section_dict)
        return {**section_dict, "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create section: {str(e)}"
        )



@router.get("/api/folders/{id}/sections", response_model=List[Section])
async def get_sections(id: str):
    try:
        # First verify the folder exists
        folder = await db.folders.find_one({"_id": ObjectId(id)})
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
        
        sections = []
        async for section in db.sections.find({"folder_id": id}):
            sections.append(prepare_document(section))
        return sections
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sections: {str(e)}"
        )

@router.get("/api/folders/{id}/sections/{section_id}", response_model=Section)
async def get_section_details(id: str, section_id: str):
    try:
        section = await db.sections.find_one({"_id": ObjectId(section_id), "folder_id": id})
        if section:
            return prepare_document(section)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve section: {str(e)}"
        )
        

@router.put("/api/folders/{id}/sections/{section_id}")
async def update_section(id: str, section_id: str, section: Section):
    try:
        update_result = await db.sections.update_one(
            {"_id": ObjectId(section_id), "folder_id": id},
            {"$set": {
                "name": section.name,
                "description": section.description
            }}
        )
        
        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        return {"message": "Section updated successfully"}
    except Exception as e:    
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update section: {str(e)}"
    )


@router.delete("/api/folders/{relative_folder_id}/sections/{section_id}")
async def delete_section(relative_folder_id: str, section_id: str):
    try:
        await db.sections.delete_one({"_id": ObjectId(section_id), "folder_id": relative_folder_id})
        return {"message": "Section deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete section: {str(e)}"
        )


@router.get("/api/folders/{relative_folder_id}/sections/{section_id}/exercises", response_model=List[Exercise])
async def get_exercises(relative_folder_id: str, section_id: str):
    try:
        # First verify the section exists
        section = await db.sections.find_one({
            "_id": ObjectId(section_id),
            "folder_id": relative_folder_id
        })
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        exercises = []
        async for exercise in db.exercises.find({"section_id": section_id}):
            exercises.append({
                "id": str(exercise.get("_id")),
                "title": exercise.get("title", ""),
                "media_url": exercise.get("media_url", ""),
                "section_id": exercise.get("section_id", ""),
                "folder_id": exercise.get("folder_id", ""),
                "description": exercise.get("description", "")
            })
        return exercises
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    except Exception as e:
        print(f"Error in get_exercises: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exercises: {str(e)}"
        )

@router.get("/api/folders/{relative_folder_id}/sections/{section_id}/exercises/{exercise_id}", response_model=Exercise)
async def get_exercise_details(relative_folder_id: str, section_id: str, exercise_id: str):
    try:
        section = await db.sections.find_one({"_id": ObjectId(section_id), "folder_id": relative_folder_id})
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )
        
        exercise = await db.exercises.find_one({"_id": ObjectId(exercise_id), "section_id": section_id})
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        return prepare_exercise(exercise)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve exercise: {str(e)}"
        )



@router.post("/api/folders/{relative_folder_id}/sections/{section_id}/exercises")
async def create_exercise_in_section(
    relative_folder_id: str, 
    section_id: str, 
    exercise: str = Form(...),
    uploaded_image: UploadFile = File(...)
):
    try:
        # Verify section exists
        section = await db.sections.find_one({
            "_id": ObjectId(section_id), 
            "folder_id": relative_folder_id
        })
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Section not found"
            )

        exercise_data = json.loads(exercise)
        
        # For serverless environment, store image in base64
        image_contents = await uploaded_image.read()
        image_base64 = base64.b64encode(image_contents).decode()
        
        exercise_dict = {
            "title": exercise_data["title"],
            "media_url": uploaded_image.filename,
            "section_id": section_id,
            "folder_id": relative_folder_id,
            "description": exercise_data.get("description", ""),
            "image_data": image_base64  # Store as base64 string
        }

        result = await db.exercises.insert_one(exercise_dict)
        
        return {
            "id": str(result.inserted_id),
            "title": exercise_dict["title"],
            "media_url": exercise_dict["media_url"],
            "section_id": exercise_dict["section_id"],
            "folder_id": exercise_dict["folder_id"],
            "description": exercise_dict["description"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exercise: {str(e)}"
        )




@router.delete("/api/folders/{relative_folder_id}/sections/{section_id}/exercises/{exercise_id}")
async def delete_exercise(relative_folder_id: str, section_id: str, exercise_id: str):
    try:
        result = await db.exercises.delete_one({
            "_id": ObjectId(exercise_id),
            "section_id": section_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
            
        return {"message": "Exercise deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete exercise: {str(e)}"
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
        # Verify exercise exists
        existing_exercise = await db.exercises.find_one({
            "_id": ObjectId(exercise_id),
            "section_id": section_id
        })
        if not existing_exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )

        # Parse exercise data
        exercise_data = json.loads(exercise)
        update_data = {
            "title": exercise_data.get("title"),
            "description": exercise_data.get("description")
        }

        # If new image is uploaded, update the image data
        if uploaded_image:
            image_contents = await uploaded_image.read()
            update_data.update({
                "media_url": uploaded_image.filename,
                "image_data": Binary(image_contents)
            })

        # Update exercise in database
        result = await db.exercises.update_one(
            {"_id": ObjectId(exercise_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found or no changes made"
            )

        return {"message": "Exercise updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update exercise: {str(e)}"
        )





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(router, host="127.0.0.1", port=8000)