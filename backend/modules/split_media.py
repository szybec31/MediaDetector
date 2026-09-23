from pathlib import Path
from datetime import datetime
import subprocess
import shutil


if shutil.which("ffmpeg") is None:
    raise RuntimeError(
        "FFmpeg nie został znaleziony w PATH."
    )


def split_media(
    project_path: Path,
    input_file: Path,
) -> tuple[Path, Path]:

    if not input_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku wejściowego:\n"
            f"{input_file}"
        )

    project_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime(
        "%d-%m-%Y_%H-%M-%S"
    )

    video_output = (
        project_path
        / f"video_{timestamp}.mp4"
    )

    audio_output = (
        project_path
        / f"audio_{timestamp}.m4a"
    )

    # Tylko video — bez ponownego kodowania.
    video_command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "copy",
        str(video_output),
    ]

    video_result = subprocess.run(
        video_command,
        capture_output=True,
        text=True,
    )

    if video_result.returncode != 0:
        raise RuntimeError(
            "Nie udało się wyodrębnić strumienia video.\n\n"
            + video_result.stderr
        )

    if not video_output.exists():
        raise RuntimeError(
            "FFmpeg zakończył działanie, "
            "ale nie utworzył pliku video."
        )

    # Tylko audio — bez ponownego kodowania.
    audio_command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-map",
        "0:a:0",
        "-vn",
        "-c:a",
        "copy",
        str(audio_output),
    ]

    audio_result = subprocess.run(
        audio_command,
        capture_output=True,
        text=True,
    )

    if audio_result.returncode != 0:
        # Jeżeli video zostało już utworzone,
        # usuwamy je, żeby nie zostawić częściowego wyniku.
        if video_output.exists():
            video_output.unlink()

        raise RuntimeError(
            "Nie udało się wyodrębnić strumienia audio.\n\n"
            + audio_result.stderr
        )

    if not audio_output.exists():
        if video_output.exists():
            video_output.unlink()

        raise RuntimeError(
            "FFmpeg zakończył działanie, "
            "ale nie utworzył pliku audio."
        )

    return video_output, audio_output