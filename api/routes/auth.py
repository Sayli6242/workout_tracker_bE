from fastapi import APIRouter, Depends
from ..auth.auth_bearer import JWTBearer
from ..models.auth import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse, dependencies=[Depends(JWTBearer())])
async def get_current_user(request: Request):
    # The user is already verified by JWTBearer and added to request.state
    return request.state.user 