from pathlib import Path
from datetime import datetime
import json
import subprocess
import shutil


# ==========================================================
# FFmpeg / FFprobe
# ==========================================================

if shutil.which("ffmpeg") is None:
    raise RuntimeError(
        "FFmpeg nie został znaleziony w PATH."
    )

if shutil.which("ffprobe") is None:
    raise RuntimeError(
        "FFprobe nie został znaleziony w PATH."
    )


# ==========================================================
# WCZYTANIE WYKRYTYCH SŁÓW
# ==========================================================

def load_detected_words(
    detected_words_file: Path,
):
    if not detected_words_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku wykrytych słów: "
            f"{detected_words_file.name}"
        )

    if detected_words_file.suffix.lower() != ".json":
        raise ValueError(
            "Plik wykrytych słów musi być plikiem JSON."
        )

    try:
        data = json.loads(
            detected_words_file.read_text(
                encoding="utf-8"
            )
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Nieprawidłowy format pliku "
            "wykrytych słów JSON."
        ) from error

    matches = data.get(
        "matches",
        []
    )

    if not isinstance(matches, list):
        raise RuntimeError(
            "Pole 'matches' w pliku JSON "
            "musi być tablicą."
        )

    return matches


# ==========================================================
# WYLICZENIE PRZEDZIAŁÓW
# ==========================================================

def merge_intervals(
    matches,
    padding: float = 0.0,
):
    intervals = []

    for match in matches:
        try:
            start = max(
                0.0,
                float(match["start"]) - padding,
            )

            end = (
                float(match["end"]) + padding
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as error:

            raise RuntimeError(
                "Nieprawidłowy przedział czasowy "
                "w pliku wykrytych słów."
            ) from error

        if end <= start:
            continue

        intervals.append(
            (
                start,
                end,
            )
        )

    if not intervals:
        return []

    intervals.sort(
        key=lambda item: item[0]
    )

    merged = [
        intervals[0]
    ]

    for start, end in intervals[1:]:

        previous_start, previous_end = (
            merged[-1]
        )

        if start <= previous_end:

            merged[-1] = (
                previous_start,
                max(
                    previous_end,
                    end,
                ),
            )

        else:

            merged.append(
                (
                    start,
                    end,
                )
            )

    return merged


# ==========================================================
# DŁUGOŚĆ PLIKU
# ==========================================================

def get_media_duration(
    input_file: Path,
) -> float:

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_file),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Nie udało się odczytać długości "
            "pliku multimedialnego.\n\n"
            + result.stderr
        )

    try:
        duration = float(
            result.stdout.strip()
        )

    except ValueError as error:

        raise RuntimeError(
            "FFprobe zwrócił nieprawidłową "
            "długość pliku."
        ) from error

    if duration <= 0:
        raise RuntimeError(
            "Plik multimedialny ma "
            "nieprawidłową długość."
        )

    return duration


# ==========================================================
# WYKRYCIE TYPU PLIKU
# ==========================================================

def is_video_file(
    input_file: Path,
) -> bool:

    video_extensions = {
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".webm",
        ".m4v",
    }

    return (
        input_file.suffix.lower()
        in video_extensions
    )


# ==========================================================
# BUDOWANIE FILTRA AUDIO
# ==========================================================

def build_mute_filter(
    intervals,
) -> str:

    filters = []

    for start, end in intervals:

        filters.append(
            "volume="
            f"enable='between(t,{start},{end})':"
            "volume=0"
        )

    if not filters:
        raise RuntimeError(
            "Nie udało się utworzyć filtra "
            "wyciszającego."
        )

    return ",".join(
        filters
    )


# ==========================================================
# WYCISZENIE WYKRYTYCH SŁÓW
# ==========================================================

def mute_detected_words(
    project_path: Path,
    input_file: Path,
    detected_words_file: Path,
    progress_callback=None,
) -> Path:

    if not input_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku wejściowego:\n"
            f"{input_file}"
        )

    if not detected_words_file.exists():
        raise FileNotFoundError(
            "Nie znaleziono pliku detected words:\n"
            f"{detected_words_file}"
        )

    results_dir = project_path

    results_dir.mkdir(
        exist_ok=True
    )

    # ======================================================
    # WCZYTANIE WYKRYTYCH SŁÓW
    # ======================================================

    matches = load_detected_words(
        detected_words_file
    )

    if not matches:
        raise RuntimeError(
            "Plik nie zawiera żadnych "
            "wykrytych słów."
        )

    # ======================================================
    # PRZEDZIAŁY
    # ======================================================

    intervals = merge_intervals(
        matches,
        padding=0.0,
    )

    if not intervals:
        raise RuntimeError(
            "Nie znaleziono prawidłowych "
            "przedziałów czasowych."
        )

    # ======================================================
    # FILTR
    # ======================================================

    filter_audio = build_mute_filter(
        intervals
    )

    # ======================================================
    # TYP PLIKU
    # ======================================================

    video = is_video_file(
        input_file
    )

    # ======================================================
    # NAZWA WYNIKU
    # ======================================================

    timestamp = datetime.now().strftime(
        "%d-%m-%Y_%H-%M-%S"
    )

    if video:

        output_file = (
            results_dir
            / f"muted_{timestamp}.mp4"
        )

    else:

        output_file = (
            results_dir
            / f"muted_{timestamp}.wav"
        )

    # ======================================================
    # DŁUGOŚĆ
    # ======================================================

    duration = get_media_duration(
        input_file
    )

    # ======================================================
    # FFmpeg
    # ======================================================

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(input_file),

        "-af",
        filter_audio,

        "-progress",
        "pipe:1",

        "-nostats",

        "-loglevel",
        "error",
    ]

    if video:

        command.extend(
            [
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

                str(output_file),
            ]
        )

    else:

        command.extend(
            [
                "-c:a",
                "pcm_s16le",

                str(output_file),
            ]
        )

    # ======================================================
    # START FFmpeg
    # ======================================================

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

        output_lines.append(
            line
        )

        if line.startswith(
            "out_time_ms="
        ):

            try:

                out_time_ms = int(
                    line.split(
                        "=",
                        1
                    )[1]
                )

                current_time = (
                    out_time_ms
                    / 1_000_000
                )

                ffmpeg_progress = (
                    current_time
                    / duration
                )

                ffmpeg_progress = min(
                    max(
                        ffmpeg_progress,
                        0.0,
                    ),
                    1.0,
                )

                # Operacja zajmuje cały zakres
                # 5%-95%.
                job_progress = (
                    0.05
                    + ffmpeg_progress * 0.90
                )

                if (
                    job_progress
                    - last_progress
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

    # ======================================================
    # BŁĄD FFmpeg
    # ======================================================

    if process.returncode != 0:

        ffmpeg_output = "\n".join(
            output_lines
        )

        raise RuntimeError(
            "FFmpeg nie mógł wyciszyć "
            "wykrytych słów.\n\n"
            + ffmpeg_output
        )

    # ======================================================
    # SPRAWDZENIE WYNIKU
    # ======================================================

    if not output_file.exists():

        raise RuntimeError(
            "FFmpeg zakończył działanie, "
            "ale nie utworzył pliku wynikowego."
        )

    if progress_callback:

        progress_callback(
            0.95
        )

    return output_file