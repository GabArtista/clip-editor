import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .config import job_storage_dir


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStateRepository:
    """Persistência baseada em arquivos JSON para estado de jobs."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or job_storage_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _job_path(self, job_id: str) -> Path:
        return self.base_dir / f"{job_id}.json"

    def create_job(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = {
            "job_id": job_id,
            "created_at": _utcnow_iso(),
            "status": "queued",
            "request": payload,
            "history": [{"status": "queued", "timestamp": _utcnow_iso(), "detail": "job enqueued"}],
            "result": None,
            "error": None,
        }
        self._write(job_id, data)
        return data

    def _read(self, job_id: str) -> Dict[str, Any]:
        path = self._job_path(job_id)
        if not path.exists():
            raise KeyError(f"Job {job_id} not found")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, job_id: str, data: Dict[str, Any]) -> None:
        path = self._job_path(job_id)
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        tmp_path.replace(path)

    def update_status(self, job_id: str, status: str, detail: Optional[Any] = None) -> Dict[str, Any]:
        with self._lock:
            data = self._read(job_id)
            entry = {"status": status, "timestamp": _utcnow_iso()}
            if detail is not None:
                entry["detail"] = detail
            data["status"] = status
            data["history"].append(entry)
            self._write(job_id, data)
            return data

    def set_result(self, job_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._read(job_id)
            data["result"] = result
            self._write(job_id, data)
            return data

    def set_error(self, job_id: str, error: str) -> Dict[str, Any]:
        with self._lock:
            data = self._read(job_id)
            data["error"] = {"message": error, "timestamp": _utcnow_iso()}
            self._write(job_id, data)
            return data

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self._read(job_id)
        except KeyError:
            return None
