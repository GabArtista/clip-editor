import os
import threading
import time
from pathlib import Path
from typing import Iterable, List, Optional


def _list_files(directory: Path) -> List[Path]:
    if not directory.exists():
        return []
    return [item for item in directory.iterdir() if item.is_file()]


def cleanup_directory(directory: Path, older_than_seconds: float) -> List[str]:
    """
    Remove arquivos mais antigos que `older_than_seconds`.
    Retorna lista de caminhos removidos (strings) para logging/testes.
    """
    removed: List[str] = []
    now = time.time()

    for file_path in _list_files(directory):
        if file_path.name.startswith("."):
            continue
        age = now - file_path.stat().st_mtime
        if age > older_than_seconds:
            try:
                file_path.unlink()
                removed.append(str(file_path))
            except OSError:
                continue
    return removed


class CleanupScheduler:
    def __init__(self, directories: Iterable[Path], older_than_seconds: float, interval_seconds: float) -> None:
        self.directories = list(directories)
        self.older_than = older_than_seconds
        self.interval = interval_seconds
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _worker() -> None:
            while True:
                for directory in self.directories:
                    cleanup_directory(directory, self.older_than)
                time.sleep(self.interval)

        self._thread = threading.Thread(target=_worker, name="cleanup-scheduler", daemon=True)
        self._thread.start()
