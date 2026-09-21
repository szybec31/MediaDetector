from dataclasses import dataclass, field
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass
class ModuleJob:
    job_id: str
    module_id: str
    project_id: int

    status: str = "pending"
    progress: float = 0.0
    message: str = ""
    output_files: list[str] = field(default_factory=list)
    error: str | None = None


_jobs: dict[str, ModuleJob] = {}
_jobs_lock = Lock()


def create_job(
    module_id: str,
    project_id: int,
) -> ModuleJob:
    job = ModuleJob(
        job_id=str(uuid4()),
        module_id=module_id,
        project_id=project_id,
    )

    with _jobs_lock:
        _jobs[job.job_id] = job

    return job


def get_job(job_id: str) -> ModuleJob | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def update_job(
    job_id: str,
    *,
    status: str | None = None,
    progress: float | None = None,
    message: str | None = None,
    output_files: list[str] | None = None,
    error: str | None = None,
) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)

        if job is None:
            return

        if status is not None:
            job.status = status

        if progress is not None:
            job.progress = min(max(progress, 0.0), 1.0)

        if message is not None:
            job.message = message

        if output_files is not None:
            job.output_files = output_files

        if error is not None:
            job.error = error