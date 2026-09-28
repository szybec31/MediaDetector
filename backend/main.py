from schemas import Project, ProjectCreate, ProfanityDictionary, ProjectDetails
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from datetime import datetime
from pathlib import Path
import tempfile
import zipfile
import shutil
import json
import re
import mimetypes

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

# Upload plików do projektu
@app.post("/api/projects/{project_id}/files")
async def upload_project_files(
    project_id: int,
    files: list[UploadFile] = File(...),
):
    project_dir = find_project_by_id(project_id)

    if project_dir is None:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="Nie przesłano żadnych plików.",
        )

    original_dir = project_dir
    original_dir.mkdir(exist_ok=True)

    project_file = project_dir / "project_info.json"

    try:
        with project_file.open("r", encoding="utf-8") as file:
            project_info = json.load(file)
    except (json.JSONDecodeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Nie można odczytać informacji o projekcie.",
        )

    if "files" not in project_info:
        project_info["files"] = []

    saved_files = []

    for uploaded_file in files:
        if not uploaded_file.filename:
            continue

        filename = Path(uploaded_file.filename).name

        if not filename:
            continue

        content_type = uploaded_file.content_type or ""

        if not (
            content_type.startswith("audio/")
            or content_type.startswith("video/")
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Plik '{filename}' nie jest plikiem "
                    "audio ani video."
                ),
            )

        destination = original_dir / filename

        if destination.exists():
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Plik o nazwie '{filename}' "
                    "już istnieje w projekcie."
                ),
            )

        try:
            with destination.open("wb") as output_file:
                shutil.copyfileobj(
                    uploaded_file.file,
                    output_file,
                )

            file_size = destination.stat().st_size

        except OSError:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Nie udało się zapisać pliku "
                    f"'{filename}'."
                ),
            )

        file_info = {
            "name": filename,
            "size": file_size,
            "type": content_type,
            "source": "original",
        }

        project_info["files"].append(file_info)
        saved_files.append(file_info)

    try:
        with project_file.open("w", encoding="utf-8") as file:
            json.dump(
                project_info,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError:
        raise HTTPException(
            status_code=500,
            detail=(
                "Pliki zostały zapisane, ale nie udało się "
                "zaktualizować project_info.json."
            ),
        )

    return {
        "message": "Pliki zostały dodane.",
        "files": saved_files,
    }


# Pobieranie pojedynczego, wszystkich plików, usunięcię
def load_project_info(project_dir: Path) -> dict:
    project_file = project_dir / "project_info.json"

    try:
        with project_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="Nie można odczytać informacji o projekcie.",
        )

def save_project_info(
    project_dir: Path,
    project_info: dict,
) -> None:
    project_file = project_dir / "project_info.json"

    try:
        with project_file.open("w", encoding="utf-8") as file:
            json.dump(
                project_info,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Nie można zapisać informacji o projekcie.",
        )

def find_project_file(
    project_dir: Path,
    filename: str,
) -> tuple[dict, Path]:
    project_info = load_project_info(project_dir)

    project_files = project_info.get("files", [])

    for file_info in project_files:
        if (
            file_info.get("name") == filename
            and file_info.get("source", "original") != "source"
        ):
            file_path = (
                project_dir
                / filename
            )

            if not file_path.exists() or not file_path.is_file():
                raise HTTPException(
                    status_code=404,
                    detail="Plik nie istnieje na dysku.",
                )

            return project_info, file_path

    raise HTTPException(
        status_code=404,
        detail="Plik nie należy do tego projektu.",
    )


@app.get(
    "/api/projects/{project_id}/files/download-all"
)
def download_all_project_files(
    project_id: int,
    background_tasks: BackgroundTasks,
):
    project_dir = find_project_by_id(project_id)

    if project_dir is None:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    project_info = load_project_info(project_dir)

    project_files = project_info.get("files", [])

    if not project_files:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie zawiera żadnych plików.",
        )

    original_dir = project_dir

    if not original_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="Folder z plikami nie istnieje.",
        )

    temporary_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".zip",
    )

    zip_path = Path(temporary_file.name)
    temporary_file.close()

    try:
        with zipfile.ZipFile(
            zip_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            added_files = 0

            for file_info in project_files:
                if file_info.get("source", "original") == "source":
                    continue

                filename = file_info.get("name")

                if not filename:
                    continue

                file_path = original_dir / filename

                if not file_path.exists() or not file_path.is_file():
                    continue

                archive.write(
                    file_path,
                    arcname=filename,
                )

                added_files += 1

        if added_files == 0:
            zip_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=404,
                detail="Nie znaleziono plików do pobrania.",
            )

    except HTTPException:
        raise

    except OSError:
        zip_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Nie udało się przygotować archiwum ZIP.",
        )

    background_tasks.add_task(
        zip_path.unlink,
        missing_ok=True,
    )

    return FileResponse(
        path=zip_path,
        filename=f"{project_info['name']}.zip",
        media_type="application/zip",
    )

@app.get("/api/projects/{project_id}/files/download/{filename}")
def download_project_file(
    project_id: int,
    filename: str,
):
    project_dir = find_project_by_id(project_id)

    if project_dir is None:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    _, file_path = find_project_file(
        project_dir,
        filename,
    )

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono pliku.",
        )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@app.delete("/api/projects/{project_id}/files/{filename}")
def delete_project_file(
    project_id: int,
    filename: str,
):
    project_dir = find_project_by_id(project_id)

    if project_dir is None:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    project_info, file_path = find_project_file(
        project_dir,
        filename,
    )

    try:
        file_path.unlink()

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Nie udało się usunąć pliku.",
        )

    project_info["files"] = [
        file_info
        for file_info in project_info.get("files", [])
        if not (
            file_info.get("name") == filename
            and file_info.get("source", "original") != "original"
        )
    ]

    save_project_info(
        project_dir,
        project_info,
    )

    return {
        "message": "Plik został usunięty.",
        "filename": filename,
    }


# --------------- Endpointy dotyczące modułów AI ---------------
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from modules.runner import run_transcription_job
from models.modules import (
    ModuleJobResponse,
    ModuleJobStatus,
    ModuleRunRequest,
)
from services.module_jobs import (
    create_job,
    get_job,
)


router = APIRouter(
    prefix="/api/modules",
    tags=["modules"],
)


@router.post(
    "/transcription/run",
    response_model=ModuleJobResponse,
)
def run_transcription(
    request: ModuleRunRequest,
    background_tasks: BackgroundTasks,
):
    project_path = find_project_by_id(request.project_id)

    if project_path is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono projektu.",
        )

    input_file = project_path / request.filename

    if not input_file.exists() or not input_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono wybranego pliku.",
        )

    if not input_file.suffix.lower() in {
        ".mp3",
        ".mp4",
        ".wav",
        ".m4a",
        ".flac",
        ".ogg",
        ".aac",
        ".wma",
    }:
        raise HTTPException(
            status_code=400,
            detail="Moduł transkrypcji obsługuje wyłącznie pliki audio i video.",
        )

    job = create_job(
        module_id="transcription",
        project_id=request.project_id,
    )

    background_tasks.add_task(
        run_transcription_job,
        job_id=job.job_id,
        project_path=project_path,
        input_file=input_file,
        parameters=request.parameters,
    )

    return ModuleJobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message="Zadanie transkrypcji zostało uruchomione.",
        output_files=[],
    )


@router.get(
    "/transcription/status/{job_id}",
    response_model=ModuleJobStatus,
)
def transcription_status(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono zadania.",
        )

    return ModuleJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        output_files=job.output_files,
        error=job.error,
    )


app.include_router(router)


from modules.runner import run_filter_words_job
@router.post(
    "/filter-words/run",
    response_model=ModuleJobResponse,
)
def run_filter_words(
    request: ModuleRunRequest,
    background_tasks: BackgroundTasks,
):
    project_path = find_project_by_id(
        request.project_id
    )

    if project_path is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono projektu.",
        )

    input_file = project_path / request.filename

    if not input_file.exists() or not input_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono wybranego pliku.",
        )

    if input_file.suffix.lower() != ".json":
        raise HTTPException(
            status_code=400,
            detail=(
                "Moduł wykrywania słów wymaga "
                "pliku JSON transkrypcji."
            ),
        )

    job = create_job(
        module_id="filter-words",
        project_id=request.project_id,
    )

    background_tasks.add_task(
        run_filter_words_job,
        job_id=job.job_id,
        project_path=project_path,
        input_file=input_file,
        parameters=request.parameters,
    )

    return ModuleJobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message="Wykrywanie słów zostało uruchomione.",
        output_files=[],
    )

@router.get(
    "/filter-words/status/{job_id}",
    response_model=ModuleJobStatus,
)

def filter_words_status(job_id: str):

    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono zadania.",
        )

    return ModuleJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        output_files=job.output_files,
        error=job.error,
    )


from modules.runner import run_censor_transcription_job
@router.post(
    "/censor-transcription/run",
    response_model=ModuleJobResponse,
)
def run_censor_transcription(
    request: ModuleRunRequest,
    background_tasks: BackgroundTasks,
):
    project_path = find_project_by_id(request.project_id)

    if project_path is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono projektu.",
        )

    # Plik wejściowy — JSON transkrypcji
    input_file = project_path / request.filename

    if not input_file.exists() or not input_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono wybranego pliku.",
        )

    if input_file.suffix.lower() != ".json":
        raise HTTPException(
            status_code=400,
            detail=(
                "Moduł cenzurowania wymaga "
                "pliku JSON transkrypcji."
            ),
        )

    # Plik z wykrytymi przekleństwami
    detected_words_filename = request.parameters.get(
        "detected_words_file"
    )

    if not detected_words_filename:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nie wskazano pliku z wykrytymi słowami."
            ),
        )

    detected_words_file = (
        project_path / detected_words_filename
    )

    if (
        not detected_words_file.exists()
        or not detected_words_file.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Nie znaleziono pliku z wykrytymi słowami."
            ),
        )

    if detected_words_file.suffix.lower() != ".json":
        raise HTTPException(
            status_code=400,
            detail=(
                "Plik z wykrytymi słowami musi być "
                "plikiem JSON."
            ),
        )

    job = create_job(
        module_id="censor-transcription",
        project_id=request.project_id,
    )

    background_tasks.add_task(
        run_censor_transcription_job,
        job_id=job.job_id,
        project_path=project_path,
        input_file=input_file,
        parameters=request.parameters,
    )

    return ModuleJobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message="Cenzurowanie transkrypcji zostało uruchomione.",
        output_files=[],
    )


@router.get(
    "/censor-transcription/status/{job_id}",
    response_model=ModuleJobStatus,
)
def censor_transcription_status(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono zadania.",
        )

    return ModuleJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        output_files=job.output_files,
        error=job.error,
    )


from modules.runner import run_add_subtitles_job

@router.post(
    "/add-subtitles/run",
    response_model=ModuleJobResponse,
)
def run_add_subtitles(
    request: ModuleRunRequest,
    background_tasks: BackgroundTasks,
):
    project_path = find_project_by_id(
        request.project_id
    )

    if project_path is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono projektu.",
        )

    input_file = project_path / request.filename

    if not input_file.exists() or not input_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono wybranego pliku.",
        )

    if input_file.suffix.lower() not in {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Moduł dodawania napisów "
                "wymaga pliku video."
            ),
        )

    job = create_job(
        module_id="add-subtitles",
        project_id=request.project_id,
    )

    background_tasks.add_task(
        run_add_subtitles_job,
        job_id=job.job_id,
        project_path=project_path,
        input_file=input_file,
        parameters=request.parameters,
    )

    return ModuleJobResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message="Dodawanie napisów zostało uruchomione.",
        output_files=[],
    )

@router.get(
    "/add-subtitles/status/{job_id}",
    response_model=ModuleJobStatus,
)
def add_subtitles_status(
    job_id: str,
):

    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono zadania.",
        )

    return ModuleJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        output_files=job.output_files,
        error=job.error,
    )

from modules.runner import run_mute_detected_words_job

@router.post(
    "/mute-detected-words/run"
)
def start_mute_detected_words(
    request: ModuleRunRequest,
    background_tasks: BackgroundTasks
):
    project_id = str(request.project_id)

    project_path = find_project_by_id(
        request.project_id
    )

    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    input_filename = request.filename

    if not input_filename:
        raise HTTPException(
            status_code=400,
            detail="Nie wskazano pliku wejściowego.",
        )

    input_file = (
        project_path
        / input_filename
    )

    if not input_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Nie znaleziono pliku wejściowego: "
                f"{input_filename}"
            ),
        )

    parameters = request.parameters or {}

    detected_words_filename = parameters.get(
        "detected_words_file"
    )

    if not detected_words_filename:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nie wskazano pliku "
                "wykrytych słów."
            ),
        )

    detected_words_file = (
        project_path
        / detected_words_filename
    )

    if not detected_words_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Nie znaleziono pliku wykrytych słów: "
                f"{detected_words_filename}"
            ),
        )

    if detected_words_file.suffix.lower() != ".json":
        raise HTTPException(
            status_code=400,
            detail=(
                "Plik wykrytych słów musi być "
                "plikiem JSON."
            ),
        )
    job = create_job(
        module_id="mute-detected-words",
        project_id=request.project_id,
    )

    background_tasks.add_task(
        run_mute_detected_words_job,
        job_id=job.job_id,
        project_path=project_path,
        input_file=input_file,
        parameters=request.parameters,
    )

    return {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "output_files": job.output_files,
        }


@router.get(
    "/mute-detected-words/status/{job_id}",
    response_model=ModuleJobStatus,
)
def mute_detected_words_status(
    job_id: str,
):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono zadania.",
        )

    return ModuleJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        output_files=job.output_files,
        error=job.error,
    )

from modules.runner import run_split_media_job

@router.post(
    "/split-media/run"
)
def start_split_media(
    request: ModuleRunRequest,
    background_tasks: BackgroundTasks,
):
    project_id = request.project_id

    project_path = find_project_by_id(
        request.project_id
    )

    if project_path is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono projektu.",
        )

    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    input_filename = request.filename

    if not input_filename:
        raise HTTPException(
            status_code=400,
            detail="Nie wskazano pliku wejściowego.",
        )

    input_file = project_path / input_filename

    if not input_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Nie znaleziono pliku wejściowego: "
                f"{input_filename}"
            ),
        )

    job = create_job(
        module_id="split-media",
        project_id=project_id,
    )

    background_tasks.add_task(
        run_split_media_job,
        job_id=job.job_id,
        project_path=project_path,
        input_file=input_file,
        parameters=request.parameters or {},
    )

    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "output_files": job.output_files,
    }

@router.get(
    "/split-media/status/{job_id}",
    response_model=ModuleJobStatus,
)
def split_media_status(
    job_id: str,
):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono zadania.",
        )

    return ModuleJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        output_files=job.output_files,
        error=job.error,
    )

from modules.runner import run_merge_media_job

@router.post(
    "/merge-media/run"
)
def start_merge_media(
    request: ModuleRunRequest,
    background_tasks: BackgroundTasks,
):
    project_id = request.project_id

    project_path = find_project_by_id(
        request.project_id
    )

    if project_path is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono projektu.",
        )

    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    input_filename = request.filename

    if not input_filename:
        raise HTTPException(
            status_code=400,
            detail="Nie wskazano pliku video.",
        )

    input_file = (
        project_path / input_filename
    )

    if not input_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Nie znaleziono pliku video: "
                f"{input_filename}"
            ),
        )

    parameters = request.parameters or {}

    audio_filename = parameters.get(
        "audio_file"
    )

    if not audio_filename:
        raise HTTPException(
            status_code=400,
            detail="Nie wskazano pliku audio.",
        )

    audio_file = (
        project_path / audio_filename
    )

    if not audio_file.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Nie znaleziono pliku audio: "
                f"{audio_filename}"
            ),
        )

    job = create_job(
        module_id="merge-media",
        project_id=project_id,
    )

    background_tasks.add_task(
        run_merge_media_job,
        job_id=job.job_id,
        project_path=project_path,
        input_file=input_file,
        parameters=parameters,
    )

    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "output_files": job.output_files,
    }



@router.get(
    "/merge-media/status/{job_id}",
    response_model=ModuleJobStatus,
)
def merge_media_status(
    job_id: str,
):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Nie znaleziono zadania.",
        )

    return ModuleJobStatus(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        output_files=job.output_files,
        error=job.error,
    )


###########################################
# Profile i zdjęcia do rozpoznawania
###########################################
import unicodedata
from datetime import datetime, timezone
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
PROFILES_DIR = BACKEND_DIR / "profiles"
PROFILES_FILE = PROFILES_DIR / "profiles.json"


class ProfileCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def normalize_name(name: str) -> str:
    """Normalizacja do sprawdzania unikalności nazw."""
    return " ".join(name.split()).casefold()


def make_safe_name(name: str) -> str:
    """Uproszczona nazwa do przyszłych nazw plików zdjęć."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_name)
    return safe_name.strip("_").lower() or "profil"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_profiles_file() -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    if not PROFILES_FILE.exists():
        save_profiles_data({
            "version": 1,
            "next_profile_id": 1,
            "profiles": [],
        })

def load_profiles_data() -> dict:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    if not PROFILES_FILE.exists():
        data = {
            "version": 1,
            "next_profile_id": 1,
            "profiles": [],
        }
        save_profiles_data(data)
        return data

    try:
        content = PROFILES_FILE.read_text(encoding="utf-8")

        # Pusty plik lub same spacje traktujemy jak brak profili.
        if not content.strip():
            data = {
                "version": 1,
                "next_profile_id": 1,
                "profiles": [],
            }
            save_profiles_data(data)
            return data

        data = json.loads(content)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Plik profiles.json zawiera niepoprawny JSON. "
                "Nie został automatycznie nadpisany."
            ),
        ) from exc

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail="Nie można odczytać pliku profiles.json.",
        ) from exc

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=500,
            detail="Nieprawidłowa struktura profiles.json.",
        )

    profiles = data.get("profiles", [])

    if not isinstance(profiles, list):
        raise HTTPException(
            status_code=500,
            detail="Pole 'profiles' w profiles.json musi być listą.",
        )

    data.setdefault("version", 1)

    # W starszym pliku może nie być next_profile_id.
    if not isinstance(data.get("next_profile_id"), int):
        existing_ids = [
            profile.get("id", 0)
            for profile in profiles
            if isinstance(profile, dict)
            and isinstance(profile.get("id"), int)
        ]
        data["next_profile_id"] = max(existing_ids, default=0) + 1

    return data


def save_profiles_data(data: dict) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = PROFILES_FILE.with_suffix(".json.tmp")

    try:
        with temp_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        temp_file.replace(PROFILES_FILE)
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Nie można zapisać pliku profiles.json.",
        )


def clean_profile_name(name: str) -> str:
    cleaned = " ".join(name.split())

    if not cleaned:
        raise HTTPException(
            status_code=422,
            detail="Nazwa profilu nie może być pusta.",
        )

    return cleaned


def find_profile(data: dict, profile_id: int) -> dict:
    for profile in data["profiles"]:
        if profile.get("id") == profile_id:
            return profile

    raise HTTPException(
        status_code=404,
        detail="Nie znaleziono profilu.",
    )


def ensure_unique_name(
    data: dict,
    name: str,
    exclude_profile_id: int | None = None,
) -> None:
    normalized = normalize_name(name)

    for profile in data["profiles"]:
        if profile.get("id") == exclude_profile_id:
            continue

        if normalize_name(profile.get("name", "")) == normalized:
            raise HTTPException(
                status_code=409,
                detail="Profil o takiej nazwie już istnieje.",
            )


def remove_profile_photos(profile: dict) -> None:
    """
    Usuwa pliki zdjęć należące do profilu.
    Akceptuje wyłącznie nazwy plików, bez ścieżek.
    """
    for photo in profile.get("photos", []):
        filename = photo.get("filename")

        if not isinstance(filename, str):
            continue

        # Zabezpieczenie przed ścieżkami spoza katalogu profili.
        if Path(filename).name != filename:
            continue

        photo_path = PROFILES_DIR / filename

        try:
            photo_path.unlink(missing_ok=True)
        except OSError:
            raise HTTPException(
                status_code=500,
                detail=f"Nie można usunąć zdjęcia: {filename}",
            )

@app.get("/api/profiles")
def get_profiles():
    data = load_profiles_data()

    result = []

    for profile in data.get("profiles", []):
        if not isinstance(profile, dict):
            continue

        photos = []

        for photo in profile.get("photos", []):
            if not isinstance(photo, dict):
                continue

            embedding = photo.get("embedding")
            if not isinstance(embedding, dict):
                embedding = {}

            photos.append({
                "id": photo.get("id"),
                "filename": photo.get("filename", ""),
                "uploaded_at": photo.get("uploaded_at"),
                "embedding_status": embedding.get("status"),
            })

        result.append({
            "id": profile.get("id"),
            "name": profile.get("name", ""),
            "created_at": profile.get("created_at"),
            "photos": photos,
        })

    return {"profiles": result}


@app.post("/api/profiles", status_code=201)
def create_profile(request: ProfileCreateRequest):
    data = load_profiles_data()

    name = clean_profile_name(request.name)
    ensure_unique_name(data, name)

    profile_id = data["next_profile_id"]
    data["next_profile_id"] = profile_id + 1

    profile = {
        "id": profile_id,
        "name": name,
        "safe_name": make_safe_name(name),
        "created_at": now_iso(),
        "photos": [],
    }

    data["profiles"].append(profile)
    save_profiles_data(data)

    return profile


@app.patch("/api/profiles/{profile_id}")
def update_profile(
    profile_id: int,
    request: ProfileUpdateRequest,
):
    data = load_profiles_data()
    profile = find_profile(data, profile_id)

    name = clean_profile_name(request.name)
    ensure_unique_name(data, name, exclude_profile_id=profile_id)

    profile["name"] = name
    profile["safe_name"] = make_safe_name(name)

    save_profiles_data(data)

    return profile


@app.delete("/api/profiles/{profile_id}")
def delete_profile(profile_id: int):
    data = load_profiles_data()
    profile = find_profile(data, profile_id)

    # Najpierw usuwamy zdjęcia przypisane do profilu.
    remove_profile_photos(profile)

    data["profiles"] = [
        item
        for item in data["profiles"]
        if item.get("id") != profile_id
    ]

    # next_profile_id pozostaje bez zmian, więc ID nie jest ponownie używane.
    save_profiles_data(data)

    return {
        "message": "Profil został usunięty.",
        "profile_id": profile_id,
    }


@app.post("/api/profiles/{profile_id}/photos", status_code=201)
async def add_profile_photos(
    profile_id: int,
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Nie przesłano żadnych zdjęć.",
        )

    data = load_profiles_data()
    profile = find_profile(data, profile_id)

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    max_file_size = 15 * 1024 * 1024  # 15 MB na zdjęcie

    # Licznik zapisujemy w profilu, żeby ID zdjęć nie były ponownie używane.
    if "next_photo_id" not in profile:
        existing_ids = [
            photo.get("id", 0)
            for photo in profile.get("photos", [])
            if isinstance(photo.get("id"), int)
        ]
        profile["next_photo_id"] = max(existing_ids, default=0) + 1

    profile.setdefault("photos", [])

    saved_files = []
    added_photos = []

    try:
        for upload in files:
            original_name = upload.filename or ""
            extension = Path(original_name).suffix.lower()

            if extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Nieobsługiwany format pliku: {original_name}. "
                        "Dozwolone formaty: JPG, PNG, WEBP."
                    ),
                )

            if not upload.content_type or not upload.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Plik nie jest obrazem: {original_name}",
                )

            content = await upload.read()

            if not content:
                raise HTTPException(
                    status_code=400,
                    detail=f"Plik jest pusty: {original_name}",
                )

            if len(content) > max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"Plik przekracza limit 15 MB: {original_name}",
                )

            photo_id = profile["next_photo_id"]
            profile["next_photo_id"] += 1

            safe_name = profile.get("safe_name") or make_safe_name(
                profile["name"]
            )

            filename = (
                f"{safe_name}_{profile_id}_{photo_id}{extension}"
            )

            # Nazwa jest generowana przez backend, a nie przyjmowana od klienta.
            destination = PROFILES_DIR / filename
            destination.write_bytes(content)
            saved_files.append(destination)

            photo = {
                "id": photo_id,
                "filename": filename,
                "uploaded_at": now_iso(),
                "embedding": {
                    "model": None,
                    "model_version": None,
                    "vector": None,
                    "status": "pending",
                },
            }

            profile["photos"].append(photo)
            added_photos.append(photo)

        save_profiles_data(data)

    except HTTPException:
        # Jeśli walidacja któregoś pliku się nie powiedzie,
        # usuwamy pliki zapisane w trakcie tego żądania.
        for path in saved_files:
            path.unlink(missing_ok=True)
        raise

    except OSError:
        for path in saved_files:
            path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Nie udało się zapisać zdjęć profilu.",
        )

    return {
        "message": "Zdjęcia zostały dodane.",
        "profile_id": profile_id,
        "photos": added_photos,
    }


@app.delete("/api/profiles/{profile_id}/photos/{photo_id}")
def delete_profile_photo(
    profile_id: int,
    photo_id: int,
):
    data = load_profiles_data()

    profile = next(
        (
            item
            for item in data.get("profiles", [])
            if isinstance(item, dict)
            and str(item.get("id")) == str(profile_id)
        ),
        None,
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nie znaleziono profilu o ID {profile_id}.",
        )

    photos = profile.get("photos", [])

    photo = next(
        (
            item
            for item in photos
            if isinstance(item, dict)
            and str(item.get("id")) == str(photo_id)
        ),
        None,
    )

    if photo is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nie znaleziono zdjęcia o ID {photo_id} "
                f"w profilu {profile_id}."
            ),
        )

    filename = photo.get("filename")

    # Najpierw weryfikujemy nazwę, by nie usunąć pliku poza katalogiem.
    photo_path = None

    if isinstance(filename, str) and filename:
        if Path(filename).name != filename:
            raise HTTPException(
                status_code=400,
                detail="Nieprawidłowa nazwa pliku zdjęcia.",
            )

        photo_path = PROFILES_DIR / filename

    # Usuwamy zdjęcie z JSON-a.
    profile["photos"] = [
        item
        for item in photos
        if not (
            isinstance(item, dict)
            and str(item.get("id")) == str(photo_id)
        )
    ]

    save_profiles_data(data)

    # Brak pliku na dysku nie blokuje usunięcia wpisu.
    if photo_path is not None:
        try:
            photo_path.unlink(missing_ok=True)
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Usunięto wpis zdjęcia z profilu, "
                    "ale nie udało się usunąć pliku z dysku."
                ),
            ) from exc

    return {
        "message": "Zdjęcie zostało usunięte.",
        "profile_id": profile_id,
        "photo_id": photo_id,
    }


@app.get("/api/profiles/photos/{filename}")
def get_profile_photo(filename: str):
    # Blokada prób odczytu plików spoza katalogu zdjęć
    if Path(filename).name != filename:
        raise HTTPException(
            status_code=400,
            detail="Nieprawidłowa nazwa pliku.",
        )

    photo_path = PROFILES_DIR / filename

    if not photo_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Nie znaleziono zdjęcia: {filename}",
        )

    return FileResponse(photo_path)


###########################################
# Moduł rozpoznawania i blurowania twarzy
###########################################