from pathlib import Path
from datetime import datetime
import json
import re


# ==========================================================
# KONFIGURACJA
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FILTER_WORDS_FILE = (
    BASE_DIR / "filter_words.json"
)


# ==========================================================
# WCZYTANIE SŁÓW
# ==========================================================

def load_filter_words() -> dict[str, str]:
    """
    Zwraca słownik:

        {
            "znormalizowane_slowo": "pl",
            "another_word": "en"
        }

    """

    if not FILTER_WORDS_FILE.exists():
        raise FileNotFoundError(
            f"Nie znaleziono pliku: {FILTER_WORDS_FILE}"
        )

    data = json.loads(
        FILTER_WORDS_FILE.read_text(
            encoding="utf-8"
        )
    )

    words: dict[str, str] = {}

    for language, language_words in data.items():

        if not isinstance(language_words, list):
            continue

        for word in language_words:

            if not isinstance(word, str):
                continue

            normalized = normalize_word(word)

            if not normalized:
                continue

            words[normalized] = language

    return words


# ==========================================================
# NORMALIZACJA
# ==========================================================

def normalize_word(word: str) -> str:
    word = word.lower().strip()

    word = re.sub(
        r"[^\wąćęłńóśźż]",
        "",
        word,
        flags=re.UNICODE,
    )

    return word


# ==========================================================
# WCZYTANIE TRANSKRYPCJI
# ==========================================================

def load_transcription(
    transcription_file: Path,
) -> dict:

    if not transcription_file.exists():
        raise FileNotFoundError(
            f"Nie znaleziono transkrypcji: "
            f"{transcription_file.name}"
        )

    if not transcription_file.is_file():
        raise ValueError(
            f"Ścieżka nie wskazuje na plik: "
            f"{transcription_file.name}"
        )

    try:
        return json.loads(
            transcription_file.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Nieprawidłowy plik JSON: "
            f"{transcription_file.name}"
        ) from error


# ==========================================================
# WYKRYWANIE
# ==========================================================

def detect_filter_words(
    project_path: Path,
    transcription_file: Path,
) -> Path:

    filter_words = load_filter_words()

    transcription = load_transcription(
        transcription_file
    )

    detected_words = []

    # ------------------------------------------------------
    # Przeszukanie segmentów i słów z timestampami
    # ------------------------------------------------------

    for segment in transcription.get(
        "segments",
        [],
    ):

        for word_data in segment.get(
            "words",
            [],
        ):

            original_word = str(
                word_data.get("word", "")
            ).strip()

            if not original_word:
                continue

            normalized = normalize_word(
                original_word
            )

            language = filter_words.get(
                normalized
            )

            if language is None:
                continue

            start = word_data.get("start")
            end = word_data.get("end")

            if start is None or end is None:
                continue

            detected_words.append(
                {
                    "word": original_word,
                    "normalized_word": normalized,
                    "language": language,
                    "start": start,
                    "end": end,
                    "duration": end - start,
                }
            )

    # ------------------------------------------------------
    # Zapis wyniku
    # ------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%d-%m-%Y_%H-%M-%S"
    )

    output_file = (
        project_path
        / f"detected_words_{timestamp}.json"
    )

    output_data = {
        "source_transcription": (
            transcription_file.name
        ),
        "filter_words_file": (
            FILTER_WORDS_FILE.name
        ),
        "detected_count": len(
            detected_words
        ),
        "matches": detected_words,
    }

    output_file.write_text(
        json.dumps(
            output_data,
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )

    return output_file