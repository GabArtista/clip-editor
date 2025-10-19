from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from filelock import FileLock, Timeout

from .config import lock_dir

_thread_lock = Lock()
_lock_file_path: Path = lock_dir() / "video_job.lock"


@contextmanager
def processing_lock(timeout: float = 1.0):
    """
    Lock de arquivo que garante execução de apenas um job pesado por vez.
    Útil para manter baixa a utilização de CPU em servidores compartilhados.
    """
    _lock_file_path.parent.mkdir(parents=True, exist_ok=True)
    file_lock = FileLock(str(_lock_file_path))

    with _thread_lock:
        try:
            file_lock.acquire(timeout=timeout)
        except Timeout as exc:
            raise TimeoutError("Não foi possível adquirir lock para processar job.") from exc

    try:
        yield
    finally:
        file_lock.release()
