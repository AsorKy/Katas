from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    email: str 
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    email:str 
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GenreCreate(BaseModel):
    name: str = Field(min_length=1)


class GenreOut(BaseModel):
    id: int
    name: str
    created_at: datetime


class ArtistsCreate(BaseModel):
    name: str = Field(min_length=1)


class ArtistsOut(BaseModel):
    id: int
    name: str
    genres: list[str]
    created_at: datetime


class ArtistStats(BaseModel):
    artist_id: int 
    song_count: int
    playlist_count: int


class SongArtistIn(BaseModel):
    artist_id: int
    role: Literal["main", "featured", "producer", "writer"]


class SongsArtistOut(BaseModel):
    artist_id: int
    name: str
    role: Literal["main", "featured", "producer", "writer"]


class SongsOut(BaseModel):
    id: int
    title: str
    duration_s: int = Field(gt=0)
    genre: GenreOut
    created_at: datetime
    artists: list[SongsArtistOut]


class PlaylistsCreate(BaseModel):
    name: str = Field(min_length=1)


class PlaylistOut(BaseModel):
    id: int
    name: str
    created_at: datetime


class PlaylistDetail(BaseModel):
    id: int
    name: str
    songs: list[SongsOut]


class PlaylistAddSong(BaseModel):
    song_id: int


class SongCreate(BaseModel):
    title: str = Field(min_length=1)
    duration_s: int = Field(gt=0)
    genre_id: int
    artists: list[SongArtistIn] = Field(min_length=1)

    @field_validator("artists")
    @classmethod
    def no_duplicate_artists(cls, v):
        ids = [a.artist_id for a in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate artist_id in artists")
        return v