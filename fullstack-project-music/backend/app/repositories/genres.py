from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


def list_genres(db: Session) -> list[models.Genre]:
    stmt = select(models.Genre).order_by(models.Genre.id)
    return list(db.scalars(stmt))

    