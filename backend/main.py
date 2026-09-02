from datetime import datetime
import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import Project, ProjectCreate, ProfanityDictionary


app = FastAPI(title="MediaDetector")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECTS_DIR = Path(__file__).resolve().parent.parent / "data"

PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

FILTER_WORDS_FILE = (Path(__file__).resolve().parent / "filter_words.json")

@app.get("/")
def root():
    return {"message": "MediaDetector API działa!"}


@app.get("/api/projects", response_model=list[Project])
def get_projects():
    projects = []

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        project_file = project_dir / "project_info.json"

        if not project_file.exists():
            continue

        with project_file.open("r", encoding="utf-8") as file:
            project = json.load(file)

        projects.append(project)

    return projects


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(project_data: ProjectCreate):
    name = project_data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Nazwa projektu nie może być pusta.",
        )

    if not re.match(r"^[a-zA-Z0-9ąćęłńóśźżĄĆĘŁŃÓŚŹŻ _.-]+$", name):
        raise HTTPException(
            status_code=400,
            detail="Nazwa projektu zawiera niedozwolone znaki.",
        )

    project_dir = PROJECTS_DIR / name

    if project_dir.exists():
        raise HTTPException(
            status_code=409,
            detail="Projekt o takiej nazwie już istnieje.",
        )

    created_at = datetime.now()

    project = Project(
        name=name,
        created_at=created_at,
    )

    project_dir.mkdir()

    project_file = project_dir / "project_info.json"

    with project_file.open("w", encoding="utf-8") as file:
        json.dump(
            project.model_dump(mode="json"),
            file,
            ensure_ascii=False,
            indent=2,
        )

    return project


#
@app.get("/api/profanity-dictionary", response_model=ProfanityDictionary)
def get_profanity_dictionary():
    if not FILTER_WORDS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Słownik nie istnieje."
        )

    with FILTER_WORDS_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    return data

@app.put(
    "/api/profanity-dictionary",
    response_model=ProfanityDictionary
)
def update_profanity_dictionary(
    dictionary: ProfanityDictionary
):
    with FILTER_WORDS_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            dictionary.model_dump(),
            file,
            ensure_ascii=False,
            indent=2
        )

    return dictionary