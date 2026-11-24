from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "sqlite:///./test.db"
    jwt_secret: str = "dev_secret"
    access_token_expire_minutes: int = 60
    max_upload_size: int = 5 * 1024 * 1024
    upload_dir: str = "uploads"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
