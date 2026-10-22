import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

models = pytest.importorskip("app.models")

TABLES = {"users", "artists", "genres", "songs", "song_artists", "playlists", "playlist_songs"}


def make_song(session, title="Uno"):
    genre = models.Genre(name=f"Genero de {title}")
    session.add(genre)
    session.flush()
    song = models.Song(title=title, duration_s=200, genre_id=genre.id)
    session.add(song)
    session.flush()
    return song


def make_artist(session, name="Ana"):
    artist = models.Artist(name=name)
    session.add(artist)
    session.flush()
    return artist


def test_tables_exist(session):
    assert set(inspect(session.get_bind()).get_table_names()) == TABLES


def test_get_db_yields_a_session():
    db = pytest.importorskip("app.db")
    gen = db.get_db()
    assert isinstance(next(gen), Session)
    gen.close()


def test_created_at_is_filled(session):
    user = models.User(email="a@b.co", password_hash="x")
    session.add(user)
    session.commit()
    assert user.created_at is not None


def test_user_email_is_unique(session):
    session.add(models.User(email="a@b.co", password_hash="x"))
    session.commit()
    session.add(models.User(email="a@b.co", password_hash="y"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_genre_name_is_unique(session):
    session.add(models.Genre(name="Rock"))
    session.commit()
    session.add(models.Genre(name="Rock"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_song_needs_an_existing_genre(session):
    session.add(models.Song(title="Huerfana", duration_s=100, genre_id=999))
    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("role", ["main", "featured", "producer", "writer"])
def test_valid_roles_are_accepted(session, role):
    song, artist = make_song(session), make_artist(session)
    session.add(models.SongArtist(song_id=song.id, artist_id=artist.id, role=role))
    session.flush()


def test_invalid_role_is_rejected(session):
    song, artist = make_song(session), make_artist(session)
    session.add(models.SongArtist(song_id=song.id, artist_id=artist.id, role="dj"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_song_artist_pair_is_unique(session):
    song, artist = make_song(session), make_artist(session)
    session.add(models.SongArtist(song_id=song.id, artist_id=artist.id, role="main"))
    session.flush()
    session.add(models.SongArtist(song_id=song.id, artist_id=artist.id, role="featured"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_playlist_needs_an_existing_owner(session):
    session.add(models.Playlist(name="Huerfana", owner_id=999))
    with pytest.raises(IntegrityError):
        session.flush()


def test_playlist_song_pair_is_unique(session):
    user = models.User(email="p@b.co", password_hash="x")
    session.add(user)
    session.flush()
    playlist = models.Playlist(name="Mi lista", owner_id=user.id)
    session.add(playlist)
    session.flush()
    song = make_song(session)
    session.add(models.PlaylistSong(playlist_id=playlist.id, song_id=song.id, position=1))
    session.flush()
    session.add(models.PlaylistSong(playlist_id=playlist.id, song_id=song.id, position=2))
    with pytest.raises(IntegrityError):
        session.flush()
