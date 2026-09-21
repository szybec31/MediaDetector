from typing import Any

from pydantic import BaseModel, Field


class ModuleRunRequest(BaseModel):
    project_id: int
    filename: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ModuleJobResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str = ""
    output_files: list[str] = Field(default_factory=list)


class ModuleJobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str = ""
    output_files: list[str] = Field(default_factory=list)
    error: str | None = None