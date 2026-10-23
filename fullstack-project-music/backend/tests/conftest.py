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


@pytest.fixture
def db_factory(tmp_path):
    """Base SQLite en un archivo temporal, con las tablas creadas.

    Devuelve una fábrica de sesiones. Se usa un archivo (no ':memory:') porque
    TestClient ejecuta los endpoints en otro hilo y cada conexión a ':memory:'
    sería una base distinta y vacía.
    """
    from sqlalchemy.orm import sessionmaker

    import app.models  # noqa: F401
    from app.db import Base, make_engine

    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def client(db_factory):
    """TestClient cuya app usa la base temporal en lugar de data/music.db."""
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def override_get_db():
        with db_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
