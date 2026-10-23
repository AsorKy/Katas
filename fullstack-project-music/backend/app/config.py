from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/music.db"
    secret_key: str = "dev-only-secret-change-me-via-env-0123456789"
    algorithm: str = "HS256"
    access_token_minutes: int = 60

    

settings = Settings()