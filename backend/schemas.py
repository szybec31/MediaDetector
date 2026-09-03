from datetime import datetime
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str


class Project(BaseModel):
    id: int
    name: str
    created_at: datetime


class ProfanityDictionary(BaseModel):
    pl: list[str]
    en: list[str]


class ProjectFile(BaseModel):
    name: str
    size: int
    type: str


class ProjectDetails(BaseModel):
    id: int
    name: str
    created_at: datetime
    files: list[ProjectFile]