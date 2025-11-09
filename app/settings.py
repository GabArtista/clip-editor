import os
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """
    Garante que .env.dev seja carregado antes de .env para permitir overrides locais.
    """
    load_dotenv(".env.dev", override=False)
    load_dotenv(".env", override=True)


@lru_cache(maxsize=1)
def get_database_url() -> str:
    _load_env()
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    if all([user, password, host, port, name]):
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

    # fallback para desenvolvimento/testes sem Postgres
    runtime_dir = Path(os.getenv("RUNTIME_BASE_DIR", "runtime"))
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{runtime_dir / 'app.db'}"


@lru_cache(maxsize=1)
def music_storage_dir() -> Path:
    _load_env()
    base = Path(os.getenv("MUSIC_STORAGE_DIR", "music_storage"))
    base.mkdir(parents=True, exist_ok=True)
    return base


@lru_cache(maxsize=1)
def video_storage_dir() -> Path:
    _load_env()
    base = Path(os.getenv("VIDEOS_DIR", "videos"))
    base.mkdir(parents=True, exist_ok=True)
    return base


@lru_cache(maxsize=1)
def processed_storage_dir() -> Path:
    _load_env()
    base = Path(os.getenv("PROCESSED_DIR", "processed"))
    base.mkdir(parents=True, exist_ok=True)
    return base


@dataclass
class AuthSettings:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


@lru_cache(maxsize=1)
def get_auth_settings() -> AuthSettings:
    _load_env()
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        # Em desenvolvimento, gera fallback determinístico por execução.
        import secrets

        secret = secrets.token_urlsafe(32)
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    return AuthSettings(secret_key=secret, algorithm=algorithm, access_token_expire_minutes=expire_minutes)


@dataclass
class AISettings:
    api_key: str | None
    text_model: str
    audio_model: str
    audio_cost_per_minute_brl: Decimal
    video_cost_per_minute_brl: Decimal
    text_cost_per_1k_tokens_brl: Decimal
    platform_fee_brl: Decimal


@lru_cache(maxsize=1)
def get_ai_settings() -> AISettings:
    _load_env()
    def _decimal(env_name: str, default: str) -> Decimal:
        return Decimal(os.getenv(env_name, default))

    return AISettings(
        api_key=os.getenv("OPENAI_API_KEY"),
        text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini"),
        audio_model=os.getenv("OPENAI_AUDIO_MODEL", "gpt-4o-mini-transcribe"),
        audio_cost_per_minute_brl=_decimal("IA_AUDIO_COST_PER_MINUTE_BRL", "0.20"),
        video_cost_per_minute_brl=_decimal("IA_VIDEO_COST_PER_MINUTE_BRL", "0.50"),
        text_cost_per_1k_tokens_brl=_decimal("IA_TEXT_COST_PER_1K_TOKENS_BRL", "0.10"),
        platform_fee_brl=_decimal("IA_PLATFORM_EXTRA_FEE_BRL", "0.30"),
    )
