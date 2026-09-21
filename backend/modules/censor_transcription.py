from pathlib import Path
from datetime import datetime
import json


def load_json_file(file_path: Path) -> dict:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Nie znaleziono pliku: {file_path.name}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Ścieżka nie wskazuje na plik: {file_path.name}"
        )

    try:
        return json.loads(
            file_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Nieprawidłowy plik JSON: {file_path.name}"
        ) from error


def normalize_word(word: str) -> str:
    return (
        word
        .strip()
        .lower()
        .strip(".,!?;:\"'()[]{}")
    )


def censor_transcription(
    project_path: Path,
    transcription_file: Path,
    detected_words_file: Path,
) -> Path:

    transcription = load_json_file(transcription_file)
    detected_words_data = load_json_file(detected_words_file)

    detected_words = detected_words_data.get("matches", [])

    # Zbiór wykrytych słów wraz ze znacznikami czasu.
    detected = {
        (
            normalize_word(str(item.get("word", ""))),
            item.get("start"),
            item.get("end"),
        )
        for item in detected_words
    }

    corrected_segments = []

    for segment in transcription.get("segments", []):
        corrected_words = []

        for word_data in segment.get("words", []):
            original_word = str(
                word_data.get("word", "")
            )

            normalized = normalize_word(original_word)

            start = word_data.get("start")
            end = word_data.get("end")

            is_detected = (
                normalized,
                start,
                end,
            ) in detected

            if is_detected:
                # Liczba gwiazdek odpowiada długości słowa.
                replacement = "*" * len(normalized)

                # Zachowujemy ewentualną spację na początku
                # słowa z Whispera.
                if original_word.startswith(" "):
                    replacement = " " + replacement

                corrected_words.append(replacement)
            else:
                corrected_words.append(original_word)

        corrected_text = "".join(corrected_words).strip()

        corrected_segment = {
            **segment,
            "text": corrected_text,
        }

        corrected_segments.append(corrected_segment)

    corrected_full_text = "\n".join(
        segment["text"]
        for segment in corrected_segments
        if segment.get("text")
    )

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    output_file = (
        project_path
        / f"censored_transcription_{timestamp}.json"
    )
    txt_file = project_path / f"censored_transcription_{timestamp}.txt"

    output_data = {
        "source_transcription": transcription_file.name,
        "source_detected_words": detected_words_file.name,
        "created_at": datetime.now().isoformat(),
        "detected_count": len(detected_words),
        "segments": corrected_segments,
    }

    txt_file.write_text(
        corrected_full_text,
        encoding="utf-8",
    )

    output_file.write_text(
        json.dumps(
            output_data,
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )

    return [txt_file, output_file]