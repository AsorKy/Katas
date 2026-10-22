from fastapi import APIRouter, HTTPException

from app.schemas import UserOut

router = APIRouter(prefix="/me", tags=["users"])

@router.get("", response_model=UserOut)
def get_current_user():
    raise HTTPException(status_code=501, detail="Not implemented")


# @router.delete("/delete", response_model=None, status_code=204)
# def delete_user():
#     raise HTTPException(status_code=501, detail="Not implemented")
