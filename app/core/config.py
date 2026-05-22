from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "FastAPI App"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fastapi_db"

    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    BACKEND_CORS_ORIGINS: list[str] = []


settings = Settings()
