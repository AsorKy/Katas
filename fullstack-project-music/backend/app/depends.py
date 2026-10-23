from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.security import decode_access_token


bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db)
) -> models.User:
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing credentials")
    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid user or email")
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user