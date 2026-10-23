"""Lección 6, Paso 2: repositorio de usuarios (sin HTTP)."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories import users as users_repo


def test_create_user_returns_user_with_generated_fields(session):
    user = users_repo.create_user(session, "ana@example.com", "hash-falso")
    assert user.id == 1
    assert user.email == "ana@example.com"
    assert user.password_hash == "hash-falso"      # el repo guarda el hash tal cual, no hashea
    assert user.created_at is not None             # lo genera la base (server_default)


def test_get_by_email_finds_the_user(session):
    created = users_repo.create_user(session, "ana@example.com", "h")
    found = users_repo.get_by_email(session, "ana@example.com")
    assert found is not None and found.id == created.id


def test_get_by_email_returns_none_when_missing(session):
    assert users_repo.get_by_email(session, "nadie@example.com") is None


def test_get_by_email_matches_the_right_user(session):
    users_repo.create_user(session, "ana@example.com", "h1")
    beto = users_repo.create_user(session, "beto@example.com", "h2")
    assert users_repo.get_by_email(session, "beto@example.com").id == beto.id


def test_duplicate_email_is_rejected_by_the_database(session):
    """Última defensa: aunque el router no comprobara nada, la columna es UNIQUE."""
    users_repo.create_user(session, "ana@example.com", "h1")
    with pytest.raises(IntegrityError):
        users_repo.create_user(session, "ana@example.com", "h2")
    session.rollback()


def test_create_user_is_committed(db_factory):
    """Otra sesión distinta (como otra petición HTTP) tiene que ver al usuario."""
    with db_factory() as s1:
        users_repo.create_user(s1, "ana@example.com", "h")
    with db_factory() as s2:
        assert users_repo.get_by_email(s2, "ana@example.com") is not None
