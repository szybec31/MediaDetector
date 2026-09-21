from pathlib import Path
from typing import Any
from services.module_jobs import update_job

from modules.transcription import transcribe_audio
from modules.detect_filter_words import detect_filter_words
from modules.censor_transcription import censor_transcription

from main import load_project_info, save_project_info


def run_transcription_job(
    *,
    job_id: str,
    project_path: Path,
    input_file: Path,
    parameters: dict[str, Any],
) -> None:
    try:
        update_job(
            job_id,
            status="running",
            progress=0.0,
            message="Ładowanie modelu Whisper...",
        )

        def progress_callback(progress: float) -> None:
            update_job(
                job_id,
                status="running",
                progress=progress,
                message="Trwa transkrypcja...",
            )

        output_paths = transcribe_audio(
            project_path=project_path,
            input_file=input_file,
            progress_callback=progress_callback,
            language=parameters.get("language", "pl"),
            beam_size=int(parameters.get("beam_size", 5)),
            vad_filter=bool(parameters.get("vad_filter", True)),
            word_timestamps=bool(
                parameters.get("word_timestamps", True)
            ),
        )

        # ---------------------------------------------------------
        # Dodanie plików wynikowych do project_info.json
        # ---------------------------------------------------------

        project_info = load_project_info(project_path)

        existing_files = project_info.get("files", [])

        existing_names = {
            file_entry.get("name")
            for file_entry in existing_files
        }

        for output_path in output_paths:
            if output_path.name in existing_names:
                continue

            existing_files.append(
                {
                    "name": output_path.name,
                    "size": output_path.stat().st_size,
                    "type": (
                        "text/plain"
                        if output_path.suffix.lower() == ".txt"
                        else "application/json"
                    ),
                    "source": "result",
                }
            )

        project_info["files"] = existing_files

        save_project_info(
            project_path,
            project_info,
        )

        # ---------------------------------------------------------
        # Zakończenie zadania
        # ---------------------------------------------------------

        update_job(
            job_id,
            status="completed",
            progress=1.0,
            message="Transkrypcja zakończona.",
            output_files=[
                output_path.name
                for output_path in output_paths
            ],
        )

    except Exception as error:
        update_job(
            job_id,
            status="failed",
            progress=0.0,
            message="Transkrypcja zakończyła się błędem.",
            error=str(error),
        )


def run_filter_words_job(
    *,
    job_id: str,
    project_path: Path,
    input_file: Path,
    parameters: dict[str, Any],
) -> None:

    try:
        update_job(
            job_id,
            status="running",
            progress=0.0,
            message="Wczytywanie transkrypcji...",
        )

        update_job(
            job_id,
            status="running",
            progress=0.2,
            message="Wczytywanie słownika...",
        )

        output_file = detect_filter_words(
            project_path=project_path,
            transcription_file=input_file,
        )

        update_job(
            job_id,
            status="running",
            progress=0.9,
            message="Zapisywanie wyników...",
        )

        # ------------------------------------------------------
        # Dodanie wyniku do project_info.json
        # ------------------------------------------------------

        # Te funkcje powinny pochodzić z istniejącego
        # modułu obsługi projektów.

        project_info = load_project_info(
            project_path
        )

        files = project_info.get(
            "files",
            []
        )

        existing_names = {
            file_entry.get("name")
            for file_entry in files
        }

        if output_file.name not in existing_names:

            files.append(
                {
                    "name": output_file.name,
                    "size": output_file.stat().st_size,
                    "type": "application/json",
                    "source": "result",
                }
            )

        project_info["files"] = files

        save_project_info(
            project_path,
            project_info,
        )

        update_job(
            job_id,
            status="completed",
            progress=1.0,
            message="Wykrywanie słów zakończone.",
            output_files=[
                output_file.name
            ],
        )

    except Exception as error:

        update_job(
            job_id,
            status="failed",
            progress=0.0,
            message="Wykrywanie słów zakończyło się błędem.",
            error=str(error),
        )
def run_censor_transcription_job(
    *,
    job_id: str,
    project_path: Path,
    input_file: Path,
    parameters: dict[str, Any],
) -> None:
    try:
        update_job(
            job_id,
            status="running",
            progress=0.0,
            message="Wczytywanie transkrypcji...",
        )

        detected_words_filename = parameters.get(
            "detected_words_file"
        )

        if not detected_words_filename:
            raise ValueError(
                "Nie wskazano pliku z wykrytymi słowami."
            )

        detected_words_file = (
            project_path / detected_words_filename
        )

        if not detected_words_file.exists():
            raise FileNotFoundError(
                "Nie znaleziono pliku z wykrytymi słowami: "
                f"{detected_words_filename}"
            )

        update_job(
            job_id,
            status="running",
            progress=0.3,
            message="Zamiana wykrytych słów na gwiazdki...",
        )

        output_files = censor_transcription(
            project_path=project_path,
            transcription_file=input_file,
            detected_words_file=detected_words_file,
        )

        update_job(
            job_id,
            status="running",
            progress=0.9,
            message="Zapisywanie wyników...",
        )

        # ------------------------------------------------------
        # Dodanie wyników do project_info.json
        # ------------------------------------------------------

        project_info = load_project_info(
            project_path
        )

        files = project_info.get(
            "files",
            []
        )

        existing_names = {
            file_entry.get("name")
            for file_entry in files
        }

        for output_file in output_files:
            if output_file.name not in existing_names:
                files.append(
                    {
                        "name": output_file.name,
                        "size": output_file.stat().st_size,
                        "type": (
                            "text/plain"
                            if output_file.suffix.lower() == ".txt"
                            else "application/json"
                        ),
                        "source": "result",
                    }
                )

        project_info["files"] = files

        save_project_info(
            project_path,
            project_info,
        )

        update_job(
            job_id,
            status="completed",
            progress=1.0,
            message="Transkrypcja została ocenzurowana.",
            output_files=[
                output_file.name
                for output_file in output_files
            ],
        )

    except Exception as error:
        update_job(
            job_id,
            status="failed",
            progress=0.0,
            message="Cenzurowanie transkrypcji zakończyło się błędem.",
            error=str(error),
        )


from modules.subtitles import add_subtitles

def run_add_subtitles_job(
    *,
    job_id: str,
    project_path: Path,
    input_file: Path,
    parameters: dict[str, Any],
) -> None:

    try:
        update_job(
            job_id,
            status="running",
            progress=0.0,
            message="Wczytywanie ustawień napisów...",
        )

        transcription_filename = parameters.get(
            "transcription_file"
        )

        if not transcription_filename:
            raise ValueError(
                "Nie wskazano pliku transkrypcji."
            )

        transcription_file = (
            project_path
            / transcription_filename
        )

        if not transcription_file.exists():
            raise FileNotFoundError(
                "Nie znaleziono pliku transkrypcji: "
                f"{transcription_filename}"
            )

        if transcription_file.suffix.lower() != ".json":
            raise ValueError(
                "Plik transkrypcji musi być plikiem JSON."
            )

        font_size = int(
            parameters.get(
                "font_size",
                24,
            )
        )

        font_color = str(
            parameters.get(
                "font_color",
                "#FFFFFF",
            )
        )

        update_job(
            job_id,
            status="running",
            progress=0.2,
            message="Generowanie napisów...",
        )

        output_file = add_subtitles(
            project_path=project_path,
            video_file=input_file,
            transcription_file=transcription_file,
            font_size=font_size,
            font_color=font_color,
        )

        update_job(
            job_id,
            status="running",
            progress=0.9,
            message="Zapisywanie wyniku...",
        )

        project_info = load_project_info(
            project_path
        )

        files = project_info.get(
            "files",
            []
        )

        existing_names = {
            file_entry.get("name")
            for file_entry in files
        }

        if output_file.name not in existing_names:
            files.append(
                {
                    "name": output_file.name,
                    "size": output_file.stat().st_size,
                    "type": "video/mp4",
                    "source": "result",
                }
            )

        project_info["files"] = files

        save_project_info(
            project_path,
            project_info,
        )

        update_job(
            job_id,
            status="completed",
            progress=1.0,
            message="Napisy zostały dodane do filmu.",
            output_files=[
                output_file.name
            ],
        )

    except Exception as error:

        update_job(
            job_id,
            status="failed",
            progress=0.0,
            message=(
                "Dodawanie napisów "
                "zakończyło się błędem."
            ),
            error=str(error),
        )