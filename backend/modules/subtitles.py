from pathlib import Path
from datetime import datetime
import json
import subprocess
import shutil
import re
import time


# ==========================================================
# FFMPEG
# ==========================================================

if shutil.which("ffmpeg") is None:
    raise RuntimeError(
        "FFmpeg nie został znaleziony w PATH."
    )


# ==========================================================
# CZAS SRT
# ==========================================================

def format_srt_time(seconds: float) -> str:

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000

    minutes = milliseconds // 60_000
    milliseconds %= 60_000

    seconds_value = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds_value:02d},"
        f"{milliseconds:03d}"
    )


# ==========================================================
# WCZYTANIE TRANSKRYPCJI
# ==========================================================

def load_transcription(
    transcription_file: Path,
):
    return json.loads(
        transcription_file.read_text(
            encoding="utf-8"
        )
    )


# ==========================================================
# GENEROWANIE SRT
# ==========================================================

def create_srt(
    project_path: Path,
    transcription_file: Path,
) -> Path:

    results_dir = project_path

    results_dir.mkdir(
        exist_ok=True
    )

    transcription = load_transcription(
        transcription_file
    )

    segments = transcription.get(
        "segments",
        []
    )

    if not segments:
        raise RuntimeError(
            "Transkrypcja nie zawiera segmentów."
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    srt_file = (
        results_dir
        / f"subtitles_{timestamp}.srt"
    )

    lines = []

    subtitle_index = 1

    for segment in segments:

        text = segment.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        start = float(
            segment["start"]
        )

        end = float(
            segment["end"]
        )

        lines.append(
            str(subtitle_index)
        )

        lines.append(
            f"{format_srt_time(start)} --> "
            f"{format_srt_time(end)}"
        )

        lines.append(text)

        lines.append("")

        subtitle_index += 1

    if subtitle_index == 1:
        raise RuntimeError(
            "Transkrypcja nie zawiera tekstu "
            "możliwego do wykorzystania jako napisy."
        )

    srt_file.write_text(
        "\n".join(lines),
        encoding="utf-8-sig"
    )

    return srt_file


# ==========================================================
# KOLOR
# ==========================================================

def hex_to_ass_color(
    color: str,
) -> str:

    color = color.strip()

    if not re.fullmatch(
        r"#[0-9a-fA-F]{6}",
        color,
    ):
        raise ValueError(
            "Nieprawidłowy kolor napisów. "
            "Użyj formatu #RRGGBB."
        )

    red = color[1:3]
    green = color[3:5]
    blue = color[5:7]

    # ASS używa kolejności BBGGRR.
    return f"&H00{blue}{green}{red}"

# ==========================================================
# Odczytanie długości video
# ==========================================================
def get_video_duration(
    video_file: Path,
) -> float:

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_file),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Nie udało się odczytać długości filmu.\n\n"
            + result.stderr
        )

    try:
        return float(result.stdout.strip())
    except ValueError:
        raise RuntimeError(
            "FFprobe zwrócił nieprawidłową długość filmu."
        )


# ==========================================================
# WTOPIENIE NAPISÓW W VIDEO
# ==========================================================
def burn_subtitles(
    project_path: Path,
    video_file: Path,
    srt_file: Path,
    font_size: int,
    font_color: str,
    progress_callback=None,
) -> Path:

    results_dir = project_path

    results_dir.mkdir(
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%d-%m-%Y_%H-%M-%S"
    )

    output_file = (
        results_dir
        / f"subtitled_{timestamp}.mp4"
    )

    if not video_file.exists():
        raise RuntimeError(
            f"Nie znaleziono pliku video:\n{video_file}"
        )

    if not srt_file.exists():
        raise RuntimeError(
            f"Nie znaleziono pliku SRT:\n{srt_file}"
        )

    if font_size < 8 or font_size > 72:
        raise ValueError(
            "Wielkość czcionki musi znajdować się "
            "w zakresie od 8 do 72."
        )

    ass_color = hex_to_ass_color(
        font_color
    )

    subtitle_path = str(
        srt_file.resolve()
    ).replace("\\", "/")

    # Zabezpieczenie ścieżki dla filtra FFmpeg.
    subtitle_path = subtitle_path.replace(
        ":",
        r"\:",
    )

    subtitle_filter = (
        f"subtitles='{subtitle_path}':"
        f"force_style="
        f"'FontSize={font_size},"
        f"PrimaryColour={ass_color}'"
    )

    duration = get_video_duration(
        video_file
    )

    if duration <= 0:
        raise RuntimeError(
            "Nie udało się odczytać poprawnej "
            "długości filmu."
        )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(video_file),

        "-vf",
        subtitle_filter,

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "18",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-progress",
        "pipe:1",

        "-nostats",

        "-loglevel",
        "error",

        str(output_file),
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    if process.stdout is None:
        process.kill()

        raise RuntimeError(
            "Nie udało się odczytać "
            "postępu FFmpeg."
        )

    last_progress = 0.0
    output_lines = []

    for line in process.stdout:
        line = line.strip()

        if not line:
            continue

        output_lines.append(line)

        if line.startswith("out_time_ms="):
            try:
                out_time_ms = int(
                    line.split("=", 1)[1]
                )

                current_time = (
                    out_time_ms / 1_000_000
                )

                ffmpeg_progress = (
                    current_time / duration
                )

                ffmpeg_progress = min(
                    max(
                        ffmpeg_progress,
                        0.0,
                    ),
                    1.0,
                )

                # FFmpeg zajmuje zakres 10%-95%.
                job_progress = (
                    0.10
                    + ffmpeg_progress * 0.85
                )

                # Aktualizujemy progress tylko,
                # gdy zmienił się przynajmniej o 0.5%.
                if (
                    job_progress - last_progress
                    >= 0.005
                ):
                    if progress_callback:
                        progress_callback(
                            job_progress
                        )

                    last_progress = (
                        job_progress
                    )

            except ValueError:
                continue

    process.wait()

    if process.returncode != 0:
        ffmpeg_output = "\n".join(
            output_lines
        )

        raise RuntimeError(
            "FFmpeg nie mógł wtopić napisów.\n\n"
            + ffmpeg_output
        )

    if not output_file.exists():
        raise RuntimeError(
            "FFmpeg zakończył działanie, "
            "ale nie utworzył pliku wynikowego."
        )

    if progress_callback:
        progress_callback(0.95)

    return output_file

# ==========================================================
# GŁÓWNA FUNKCJA
# ==========================================================
def add_subtitles(
    *,
    project_path: Path,
    video_file: Path,
    transcription_file: Path,
    font_size: int,
    font_color: str,
    progress_callback=None,
) -> tuple[Path, Path]:

    srt_file = create_srt(
        project_path=project_path,
        transcription_file=transcription_file,
    )

    output_file = burn_subtitles(
        project_path=project_path,
        video_file=video_file,
        srt_file=srt_file,
        font_size=font_size,
        font_color=font_color,
        progress_callback=progress_callback,
    )

    return output_file, srt_file