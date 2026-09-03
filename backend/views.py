from datetime import datetime
import json
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import Project, ProjectCreate, ProfanityDictionary, ProjectDetails
import shutil

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

# Pobranie listy istniejących projektów
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

# Wyznaczenie następnego id na podstawie już istniejących projektów
def get_next_project_id() -> int:
    max_id = 0

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        project_file = project_dir / "project_info.json"

        if not project_file.exists():
            continue

        try:
            with project_file.open(
                "r",
                encoding="utf-8"
            ) as file:
                project_info = json.load(file)

            project_id = project_info.get("id")

            if isinstance(project_id, int):
                max_id = max(max_id, project_id)

        except (json.JSONDecodeError, OSError):
            continue

    return max_id + 1

# Utworzenie nowego projektu
@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(project_data: ProjectCreate):
    name = project_data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Nazwa projektu nie może być pusta.",
        )

    if not re.match(
        r"^[a-zA-Z0-9ąćęłńóśźżĄĆĘŁŃÓŚŹŻ _.-]+$",
        name,
    ):
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

    project_id = get_next_project_id()
    created_at = datetime.now()

    project = Project(
        id=project_id,
        name=name,
        created_at=created_at,
    )

    project_dir.mkdir()

    project_file = project_dir / "project_info.json"

    project_info = {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at,
        "files": [],
    }

    with project_file.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            project.model_dump(mode="json")
            | {"files": []},
            file,
            ensure_ascii=False,
            indent=2,
        )

    return project
# --------------- Endpointy do słownika ---------------

# Wyświetlenie słownika zawierającego słowa do filtrowania
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

# Modyfikacja słownika
@app.put("/api/profanity-dictionary",response_model=ProfanityDictionary)
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



def get_file_type(file_name: str) -> str:
    extension = Path(file_name).suffix.lower()

    if extension in {".mp4", ".avi", ".mkv", ".mov", ".webm"}:
        return "video"

    if extension in {".mp3", ".wav", ".flac", ".ogg", ".m4a"}:
        return "audio"

    if extension == ".txt":
        return "text"

    if extension == ".json":
        return "json"

    return "other"

# --------------- Endpointy danego projektu ---------------

# Znalezienie wybranego projektu po jego id
def find_project_by_id(project_id: int) -> Path | None:
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        project_file = project_dir / "project_info.json"

        if not project_file.exists():
            continue

        try:
            with project_file.open(
                "r",
                encoding="utf-8"
            ) as file:
                project_info = json.load(file)

            if project_info.get("id") == project_id:
                return project_dir

        except (json.JSONDecodeError, OSError):
            continue

    return None

# wyświetlenie szczegółów danego projektu
@app.get("/api/projects/{project_id}",response_model=ProjectDetails,)
def get_project(project_id: int):
    project_dir = find_project_by_id(project_id)

    if project_dir is None:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    project_file = project_dir / "project_info.json"

    with project_file.open(
        "r",
        encoding="utf-8"
    ) as file:
        project_info = json.load(file)

    return project_info

# usunięcie wybranego projektu
@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int):
    project_dir = find_project_by_id(project_id)

    if project_dir is None:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    shutil.rmtree(project_dir)

    return {
        "message": "Projekt został usunięty."
    }

# --------------- Endpointy dotyczące akcji na plikach ---------------