import uuid
from typing import Any, Dict, Optional

from rq import Queue
from rq.job import Job

from .config import get_env_int, job_execution_mode, redis_connection
from .state import JobStateRepository
from .tasks import process_video_job


class JobManager:
    """Interface de alto nível para enfileirar e consultar jobs."""

    def __init__(self) -> None:
        self.mode = job_execution_mode()
        self.repo = JobStateRepository()
        self.redis = redis_connection()
        self.queue: Optional[Queue]
        if self.mode == "async":
            queue_name = "video-edit"
            timeout = get_env_int("JOB_TIMEOUT_SECONDS", 1800)
            self.queue = Queue(queue_name, connection=self.redis, default_timeout=timeout)
        else:
            self.queue = None

    def enqueue_video_edit(self, payload: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        self.repo.create_job(job_id, payload)

        if self.mode == "sync":
            process_video_job(job_id=job_id, payload=payload)
        else:
            assert self.queue is not None  # para mypy
            self.queue.enqueue_call(
                func=process_video_job,
                kwargs={"job_id": job_id, "payload": payload},
                job_id=job_id,
            )

        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        job_data = self.repo.get_job(job_id)
        if job_data is not None:
            return job_data

        if self.mode == "async":
            try:
                rq_job: Job = Job.fetch(job_id, connection=self.redis)
                return {
                    "job_id": job_id,
                    "status": rq_job.get_status(),
                    "created_at": rq_job.created_at.isoformat() if rq_job.created_at else None,
                    "enqueued_at": rq_job.enqueued_at.isoformat() if rq_job.enqueued_at else None,
                }
            except Exception:
                return None
        return None
