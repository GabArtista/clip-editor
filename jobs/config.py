import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from redis import Redis


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache(maxsize=1)
def runtime_dir() -> Path:
    """Diretório base para artefatos em tempo de execução."""
    base = Path(os.getenv("RUNTIME_BASE_DIR", "runtime"))
    return _ensure_dir(base)


@lru_cache(maxsize=1)
def job_storage_dir() -> Path:
    """Diretório onde os estados dos jobs são persistidos."""
    return _ensure_dir(runtime_dir() / "jobs")


@lru_cache(maxsize=1)
def lock_dir() -> Path:
    """Diretório utilizado para locks baseados em arquivo."""
    return _ensure_dir(runtime_dir() / "locks")


def get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def get_env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def job_execution_mode() -> str:
    mode = os.getenv("JOB_EXECUTION_MODE", "async").lower()
    return "sync" if mode == "sync" else "async"


def _should_use_fake_redis(redis_url: Optional[str]) -> bool:
    if os.getenv("FAKE_REDIS", "").lower() in {"1", "true", "yes"}:
        return True
    return not redis_url


@lru_cache(maxsize=1)
def redis_connection() -> Redis:
    """
    Retorna conexão Redis compartilhada. Usa fakeredis quando nenhum REDIS_URL está configurado
    ou a flag FAKE_REDIS=1 estiver definida, permitindo testes sem serviço externo.
    """
    redis_url = os.getenv("REDIS_URL")
    if _should_use_fake_redis(redis_url):
        from fakeredis import FakeStrictRedis

        return FakeStrictRedis(decode_responses=True)

    return Redis.from_url(redis_url, decode_responses=True)
