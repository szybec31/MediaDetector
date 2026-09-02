from datetime import datetime
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str


class Project(BaseModel):
    name: str
    created_at: datetime


class ProfanityDictionary(BaseModel):
    pl: list[str]
    en: list[str]