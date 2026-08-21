from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DeployPilot API"
    environment: str = "development"
    database_url: str = "sqlite:///./deploypilot.db"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] | str = ["http://localhost:3000"]
    auth_disabled: bool = True
    jwt_secret: str = "development-only-secret-change-this"
    jwt_algorithm: str = "HS256"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
