from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Clip Editor API"
    APP_VERSION: str = "2.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8060
    APP_WORKERS: int = 2
    DEBUG: bool = False
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "clip_editor"
    DB_PASSWORD: str = "clip_editor_pass"
    DB_NAME: str = "clip_editor_db"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    
    # Paths
    VIDEOS_DIR: str = "videos"
    PROCESSED_DIR: str = "processed"
    MUSIC_DIR: str = "music"
    COOKIES_DIR: str = "cookies"
    
    # External Services
    N8N_WEBHOOK_URL: str = "https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76"
    
    # AWS S3
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # Video Edit Settings
    VIDEO_PREVIEW_EXPIRATION_MINUTES: int = 5  # Preview expira em 5 minutos
    VIDEO_DELETE_AFTER_PUBLICATION_HOURS: int = 3  # Deleta 3h após publicação
    
    # Session
    SESSION_FILE_PATH: str = "cookies/session.netscape"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global
settings = Settings()
