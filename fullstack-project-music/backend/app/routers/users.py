from fastapi import APIRouter, Depends

from app.schemas import UserOut
from app import models
from app.depends import current_user 


router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserOut)
def get_current_user(user: models.User = Depends(current_user)):
    return user
# @router.delete("/delete", response_model=None, status_code=204)
# def delete_user():
#     raise HTTPException(status_code=501, detail="Not implemented")
