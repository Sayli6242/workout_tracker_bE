from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from typing import List
from ..config.database import pocketbase
from ..models.exercise import (
    FolderCreate, FolderResponse,
    SectionCreate, SectionResponse,
    ExerciseCreate, ExerciseResponse
)
from api.auth.auth_bearer import JWTBearer
import requests
import datetime
from fastapi import Path

router = APIRouter()

# ── FOLDER ROUTES ─────────────────────────────────────────────────────────────

@router.get("/folders/", response_model=List[FolderResponse], dependencies=[Depends(JWTBearer())])
async def get_folders(current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("folders", token=token).eq("user_id", user_id).execute()
        return result.get("items", [])
    except Exception as e:
        print(f"Error getting folders: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/folders/{folder_id}", response_model=FolderResponse, dependencies=[Depends(JWTBearer())])
async def get_folder(folder_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not result.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/folders/", response_model=FolderResponse, dependencies=[Depends(JWTBearer())])
async def create_folder(folder: FolderCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        data = {"name": folder.name, "user_id": user_id}
        print(f"Creating folder: {data}")

        result = pocketbase.table("folders", token=token).insert(data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail=f"Failed to create folder: {result.get('error')}")

        print(f"Folder created: {result['items'][0]}")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating folder: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/folders/{id}/", response_model=FolderResponse, dependencies=[Depends(JWTBearer())])
async def update_folder(id: str, folder: FolderCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        existing = pocketbase.table("folders", token=token).eq("id", id).eq("user_id", user_id).execute()
        if not existing.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")

        result = pocketbase.table("folders", token=token).update({"name": folder.name, "id": id})
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to update folder")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/folders/{id}/", response_model=bool, dependencies=[Depends(JWTBearer())])
async def delete_folder(id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        result = pocketbase.table("folders", token=token).eq("id", id).eq("user_id", user_id).delete()
        return len(result.get("items", [])) > 0
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── SECTION ROUTES ────────────────────────────────────────────────────────────

@router.get("/folders/{folder_id}/sections/", response_model=List[SectionResponse], dependencies=[Depends(JWTBearer())])
async def get_sections(folder_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")

        result = pocketbase.table("sections", token=token).eq("folder_id", folder_id).execute()
        return result.get("items", [])
    except HTTPException:
        raise
    except Exception as e:
        print("Error getting sections:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/folders/{folder_id}/sections/{section_id}/", response_model=SectionResponse, dependencies=[Depends(JWTBearer())])
async def get_section(folder_id: str, section_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")

        result = pocketbase.table("sections", token=token).eq("id", section_id).execute()
        if not result.get("items"):
            raise HTTPException(status_code=404, detail="Section not found")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        print("Error getting section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/folders/{folder_id}/sections/", response_model=SectionResponse, dependencies=[Depends(JWTBearer())])
async def create_section(folder_id: str, section: SectionCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")

        section_data = {
            "name": section.name,
            "description": section.description or "",
            "folder_id": folder_id,
        }
        result = pocketbase.table("sections", token=token).insert(section_data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail=f"Failed to create section: {result.get('error')}")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        print("Error creating section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/folders/{folder_id}/sections/{section_id}/", response_model=SectionResponse, dependencies=[Depends(JWTBearer())])
async def update_section(folder_id: str, section_id: str, section: SectionCreate, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")

        result = pocketbase.table("sections", token=token).update({
            "id": section_id,
            "name": section.name,
            "description": section.description or "",
        })
        if not result.get("items"):
            raise HTTPException(status_code=400, detail=f"Failed to update section: {result.get('error')}")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        print("Error updating section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/folders/{folder_id}/sections/{section_id}/", dependencies=[Depends(JWTBearer())])
async def delete_section(folder_id: str, section_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")

        result = pocketbase.table("sections", token=token).eq("id", section_id).delete()
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        print("Error deleting section:", str(e))
        raise HTTPException(status_code=400, detail=str(e))

# ── EXERCISE ROUTES ───────────────────────────────────────────────────────────

@router.get("/folders/{folder_id}/sections/{section_id}/exercises/", response_model=List[ExerciseResponse], dependencies=[Depends(JWTBearer())])
async def get_exercises(folder_id: str, section_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")
        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=404, detail="Folder not found")

        result = pocketbase.table("exercise", token=token).eq("section_id", section_id).execute()
        return result.get("items", [])
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching exercises: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/folders/{folder_id}/sections/{section_id}/exercises/", response_model=ExerciseResponse)
async def create_exercise(
    folder_id: str = Path(...),
    section_id: str = Path(...),
    name: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    current_user: dict = Depends(JWTBearer())
):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")

        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=403, detail="Not authorized")

        if image:
            files = {"image": (image.filename, await image.read(), image.content_type)}
            upload_response = requests.post(
                "http://127.0.0.1:8090/api/collections/exercise/records",
                files=files,
                data={"name": name, "description": description or "", "section_id": section_id},
                headers={"Authorization": f"Bearer {token}"}
            )
            result = upload_response.json()
            if "id" in result:
                return result
            raise HTTPException(status_code=400, detail=f"Failed to upload exercise: {result}")

        exercise_data = {
            "section_id": section_id,
            "name": name,
            "description": description or ""
        }
        result = pocketbase.table("exercise", token=token).insert(exercise_data)
        if not result.get("items"):
            raise HTTPException(status_code=400, detail="Failed to create exercise")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating exercise: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/folders/{folder_id}/sections/{section_id}/exercises/{exercise_id}/", response_model=ExerciseResponse)
async def update_exercise(
    folder_id: str = Path(...),
    section_id: str = Path(...),
    exercise_id: str = Path(...),
    name: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    current_user: dict = Depends(JWTBearer())
):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")

        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=403, detail="Not authorized")

        if image:
            files = {"image": (image.filename, await image.read(), image.content_type)}
            upload_response = requests.patch(
                f"http://127.0.0.1:8090/api/collections/exercise/records/{exercise_id}",
                files=files,
                data={"name": name, "description": description or ""},
                headers={"Authorization": f"Bearer {token}"}
            )
            result = upload_response.json()
            if "id" in result:
                return result
            raise HTTPException(status_code=400, detail=f"Failed to update exercise: {result}")

        result = pocketbase.table("exercise", token=token).update({
            "id": exercise_id,
            "name": name,
            "description": description or ""
        })
        if not result.get("items"):
            raise HTTPException(status_code=400, detail=f"Failed to update exercise: {result.get('error')}")
        return result["items"][0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating exercise: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/folders/{folder_id}/sections/{section_id}/exercises/{exercise_id}/", dependencies=[Depends(JWTBearer())])
async def delete_exercise(folder_id: str, section_id: str, exercise_id: str, current_user: dict = Depends(JWTBearer())):
    try:
        token = current_user.get("_token")
        user_id = current_user.get("id")

        folder = pocketbase.table("folders", token=token).eq("id", folder_id).eq("user_id", user_id).execute()
        if not folder.get("items"):
            raise HTTPException(status_code=403, detail="Not authorized")

        result = pocketbase.table("exercise", token=token).eq("id", exercise_id).delete()
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting exercise: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}
