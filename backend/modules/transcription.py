from datetime import datetime
from pathlib import Path
import json

from faster_whisper import WhisperModel


MODEL_SIZE = "small"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

_model = None


def get_model() -> WhisperModel:
    global _model

    if _model is None:
        _model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
        )

    return _model


def transcribe_audio(
    project_path: Path,
    input_file: Path,
    progress_callback=None,
    language: str = "pl",
    beam_size: int = 5,
    vad_filter: bool = True,
    word_timestamps: bool = True,
) -> list[Path]:
    """
    Wykonuje transkrypcję i zapisuje pliki wynikowe
    bezpośrednio w katalogu projektu.

    Zwraca listę utworzonych plików.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Nie znaleziono pliku wejściowego: {input_file.name}"
        )

    if not input_file.is_file():
        raise ValueError(
            f"Ścieżka nie wskazuje na plik: {input_file.name}"
        )

    model = get_model()

    segments, info = model.transcribe(
        str(input_file),
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
        word_timestamps=word_timestamps,
    )

    transcription_segments = []
    full_text = []

    total_duration = info.duration or 0.0

    for index, segment in enumerate(segments):
        words = []

        if segment.words:
            for word in segment.words:
                words.append(
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                    }
                )

        segment_data = {
            "id": index,
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "words": words,
        }

        transcription_segments.append(segment_data)
        full_text.append(segment.text.strip())

        if progress_callback is not None and total_duration > 0:
            progress = segment.end / total_duration
            progress = min(max(progress, 0.0), 1.0)

            progress_callback(progress)

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    txt_path = project_path / f"transcription_{timestamp}.txt"
    json_path = project_path / f"transcription_{timestamp}.json"

    txt_content = "\n".join(full_text)

    txt_path.write_text(
        txt_content,
        encoding="utf-8",
    )

    json_data = {
        "source_file": input_file.name,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "model": MODEL_SIZE,
        "created_at": datetime.now().isoformat(),
        "segments": transcription_segments,
    }

    json_path.write_text(
        json.dumps(
            json_data,
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )

    return [txt_path, json_path]