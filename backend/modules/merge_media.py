from pathlib import Path
from datetime import datetime
import subprocess
import shutil


if shutil.which("ffmpeg") is None:
    raise RuntimeError(
        "FFmpeg nie został znaleziony w PATH."
    )


def merge_media(
    project_path: Path,
    video_file: Path,
    audio_file: Path,
) -> Path:

    if not video_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku video:\n"
            f"{video_file}"
        )

    if not audio_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku audio:\n"
            f"{audio_file}"
        )

    project_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime(
        "%d-%m-%Y_%H-%M-%S"
    )

    output_file = (
        project_path
        / f"merged_{timestamp}.mp4"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_file),
        "-i",
        str(audio_file),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-shortest",
        str(output_file),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Nie udało się połączyć video i audio.\n\n"
            + result.stderr
        )

    if not output_file.exists():
        raise RuntimeError(
            "FFmpeg zakończył działanie, "
            "ale nie utworzył pliku wynikowego."
        )

    return output_file