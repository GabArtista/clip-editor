import os
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
