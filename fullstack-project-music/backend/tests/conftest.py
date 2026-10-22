import pytest


@pytest.fixture
def session():
    """Base SQLite en memoria, con las tablas creadas, nueva para cada test."""
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa: F401  (registra las tablas en Base)
    from app.db import Base, make_engine

    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as s:
        yield s
    engine.dispose()
