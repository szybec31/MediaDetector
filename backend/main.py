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

@app.get(
    "/api/projects/{project_id}/files/download/{filename}"
)
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

@app.get("/api/projects/{project_id}/files/download/{filename}")
def download_project_file(project_id: int, filename: str):
    project_dir = find_project_by_id(project_id)

    if project_dir is None:
        raise HTTPException(
            status_code=404,
            detail="Projekt nie istnieje.",
        )

    _, file_path = find_project_file(project_dir, filename)

    media_type, _ = mimetypes.guess_type(file_path.name)

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type or "application/octet-stream",
    )



# --------------- Endpointy dotyczące modułów AI ---------------
from pathlib import Path
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