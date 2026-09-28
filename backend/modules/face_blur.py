from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
import shutil
import time

import cv2
import numpy as np
import insightface
import onnxruntime as ort


# ==========================================================
# PARAMETRY DOMYŚLNE
# ==========================================================

DEFAULT_PARAMETERS = {
    "provider": "auto",              # auto | cuda | cpu
    "det_size": 960,                 # 640 | 800 | 960 | 1280
    "recognition_threshold": 0.45,   # 0.0 - 1.0
    "blur_padding": 0.35,            # 0.0 - 1.0
    "blur_kernel": 51,               # nieparzysty, np. 31/51/71
    "ffmpeg_preset": "veryfast",     # ultrafast ... veryslow
    "ffmpeg_crf": 20,                # 0 - 51, niżej = lepsza jakość
}

ALLOWED_DET_SIZES = {640, 800, 960, 1280}

ALLOWED_PRESETS = {
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
}


# ==========================================================
# WALIDACJA PARAMETRÓW
# ==========================================================

def get_parameters(parameters: dict | None) -> dict:
    """
    Łączy parametry przekazane przez API z wartościami domyślnymi.
    Waliduje wartości przed uruchomieniem przetwarzania.
    """

    result = DEFAULT_PARAMETERS.copy()
    if parameters:
        result.update(parameters)

    result["provider"] = str(result["provider"]).lower()

    if result["provider"] not in {"auto", "cuda", "cpu"}:
        raise ValueError(
            "provider musi mieć wartość: auto, cuda lub cpu."
        )

    result["det_size"] = int(result["det_size"])
    if result["det_size"] not in ALLOWED_DET_SIZES:
        raise ValueError(
            f"det_size musi być jedną z wartości: "
            f"{sorted(ALLOWED_DET_SIZES)}."
        )

    result["recognition_threshold"] = float(
        result["recognition_threshold"]
    )
    if not 0.0 <= result["recognition_threshold"] <= 1.0:
        raise ValueError(
            "recognition_threshold musi być z zakresu 0–1."
        )

    result["blur_padding"] = float(result["blur_padding"])
    if not 0.0 <= result["blur_padding"] <= 1.0:
        raise ValueError(
            "blur_padding musi być z zakresu 0–1."
        )

    result["blur_kernel"] = int(result["blur_kernel"])
    if result["blur_kernel"] < 3:
        raise ValueError("blur_kernel musi wynosić co najmniej 3.")

    # Kernel Gaussa musi być nieparzysty.
    if result["blur_kernel"] % 2 == 0:
        result["blur_kernel"] += 1

    result["ffmpeg_preset"] = str(result["ffmpeg_preset"])
    if result["ffmpeg_preset"] not in ALLOWED_PRESETS:
        raise ValueError(
            f"Nieobsługiwany preset FFmpeg: "
            f"{result['ffmpeg_preset']}."
        )

    result["ffmpeg_crf"] = int(result["ffmpeg_crf"])
    if not 0 <= result["ffmpeg_crf"] <= 51:
        raise ValueError("ffmpeg_crf musi być z zakresu 0–51.")

    return result


# ==========================================================
# INSIGHTFACE / PROVIDER
# ==========================================================

def create_face_analyzer(parameters: dict):
    """
    Tworzy model InsightFace.

    auto:
        CUDA, jeśli jest dostępne, w przeciwnym razie CPU.

    cuda:
        Wymaga dostępnego CUDAExecutionProvider.

    cpu:
        Wymusza CPUExecutionProvider.
    """

    available = ort.get_available_providers()
    requested = parameters["provider"]

    if requested == "cuda":
        if "CUDAExecutionProvider" not in available:
            raise RuntimeError(
                "Wybrano CUDA, ale ONNX Runtime nie udostępnia "
                "CUDAExecutionProvider. Sprawdź instalację "
                "onnxruntime-gpu i zgodność CUDA/cuDNN."
            )

        providers = [
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ]
        ctx_id = 0

    elif requested == "cpu":
        providers = ["CPUExecutionProvider"]
        ctx_id = -1

    else:
        if "CUDAExecutionProvider" in available:
            providers = [
                "CUDAExecutionProvider",
                "CPUExecutionProvider",
            ]
            ctx_id = 0
        else:
            providers = ["CPUExecutionProvider"]
            ctx_id = -1

    analyzer = insightface.app.FaceAnalysis(
        name="buffalo_l",
        providers=providers,
    )

    det_size = parameters["det_size"]
    analyzer.prepare(
        ctx_id=ctx_id,
        det_size=(det_size, det_size),
    )

    return analyzer, providers


# ==========================================================
# EMBEDDINGI
# ==========================================================

def normalize_embedding(embedding):
    embedding = np.asarray(embedding, dtype=np.float32)
    norm = np.linalg.norm(embedding)

    if norm < 1e-8:
        return None

    return embedding / norm


def cosine_similarity(embedding_a, embedding_b) -> float:
    a = normalize_embedding(embedding_a)
    b = normalize_embedding(embedding_b)

    if a is None or b is None:
        return -1.0

    return float(np.dot(a, b))


# ==========================================================
# ZDJĘCIA REFERENCYJNE
# ==========================================================

def load_reference_embeddings(
    analyzer,
    reference_dir: Path,
) -> list[dict]:
    """
    Ładuje zdjęcia referencyjne z przekazanego katalogu.

    Każde zdjęcie powinno zawierać dokładnie jedną twarz.
    """

    if not reference_dir.exists():
        raise RuntimeError(
            f"Nie znaleziono katalogu zdjęć referencyjnych: "
            f"{reference_dir}"
        )

    extensions = {
        ".jpg", ".jpeg", ".png", ".webp", ".bmp"
    }

    image_files = sorted(
        path
        for path in reference_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in extensions
    )

    if not image_files:
        raise RuntimeError(
            "Nie znaleziono zdjęć referencyjnych."
        )

    references = []

    for image_path in image_files:
        image = cv2.imread(str(image_path))

        if image is None:
            continue

        faces = analyzer.get(image)

        # Nie używamy zdjęć bez twarzy ani z wieloma twarzami.
        if len(faces) != 1:
            continue

        embedding = normalize_embedding(faces[0].embedding)

        if embedding is None:
            continue

        references.append({
            "path": image_path,
            "embedding": embedding,
        })

    if not references:
        raise RuntimeError(
            "Nie udało się załadować prawidłowych zdjęć "
            "referencyjnych. Sprawdź, czy każde zdjęcie "
            "zawiera jedną dobrze widoczną twarz."
        )

    return references


# ==========================================================
# ROZPOZNAWANIE
# ==========================================================

def find_best_reference(face_embedding, references):
    face_embedding = normalize_embedding(face_embedding)

    if face_embedding is None:
        return None, -1.0

    best_reference = None
    best_similarity = -1.0

    for reference in references:
        similarity = cosine_similarity(
            face_embedding,
            reference["embedding"],
        )

        if similarity > best_similarity:
            best_similarity = similarity
            best_reference = reference

    return best_reference, best_similarity


def is_known_person(
    face,
    references,
    recognition_threshold: float,
):
    reference, similarity = find_best_reference(
        face.embedding,
        references,
    )

    # Brak poprawnego embeddingu oznacza osobę nieznaną.
    matched = (
        reference is not None
        and similarity >= recognition_threshold
    )

    return matched, similarity, reference


# ==========================================================
# ROZMYWANIE
# ==========================================================

def blur_face(
    frame,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    padding: float,
    blur_kernel: int,
):
    height, width = frame.shape[:2]

    face_width = max(1, x2 - x1)
    face_height = max(1, y2 - y1)

    pad_x = int(face_width * padding)
    pad_y = int(face_height * padding)

    left = max(0, x1 - pad_x)
    top = max(0, y1 - pad_y)
    right = min(width, x2 + pad_x)
    bottom = min(height, y2 + pad_y)

    if right <= left or bottom <= top:
        return

    region = frame[top:bottom, left:right]

    if region.size == 0:
        return

    kernel = blur_kernel

    # Dopasuj kernel do rozmiaru obszaru.
    max_kernel = min(region.shape[0], region.shape[1])

    if max_kernel < 3:
        return

    if kernel > max_kernel:
        kernel = max_kernel

    if kernel % 2 == 0:
        kernel -= 1

    if kernel < 3:
        return

    blurred = cv2.GaussianBlur(
        region,
        (kernel, kernel),
        0,
    )

    frame[top:bottom, left:right] = blurred


# ==========================================================
# DETEKCJA I ROZPOZNAWANIE TWARZY
# ==========================================================

def process_faces(
    analyzer,
    frame,
    references,
    recognition_threshold: float,
):
    faces = analyzer.get(frame)
    results = []

    frame_height, frame_width = frame.shape[:2]

    for face in faces:
        bbox = face.bbox

        if bbox is None:
            continue

        x1, y1, x2, y2 = map(int, bbox)

        # Ogranicz ramkę do granic obrazu.
        x1 = max(0, min(x1, frame_width - 1))
        y1 = max(0, min(y1, frame_height - 1))
        x2 = max(0, min(x2, frame_width))
        y2 = max(0, min(y2, frame_height))

        if x2 <= x1 or y2 <= y1:
            continue

        matched, similarity, reference = is_known_person(
            face,
            references,
            recognition_threshold,
        )

        results.append({
            "bbox": (x1, y1, x2, y2),
            "matched": matched,
            "similarity": similarity,
            "reference": reference,
        })

    return results


# ==========================================================
# GŁÓWNA FUNKCJA MODUŁU
# ==========================================================

def selective_face_blur(
    project_path: Path,
    input_file: Path,
    reference_dir: Path,
    parameters: dict | None = None,
    progress_callback=None,
) -> Path:
    """
    Rozpoznaje twarze i rozmywa twarze niedopasowane
    do przekazanych zdjęć referencyjnych.

    Wszystkie pliki wynikowe zapisuje bezpośrednio
    w katalogu projektu.

    progress_callback:
        funkcja(current_frame, total_frames)
    """

    project_path = Path(project_path).resolve()
    input_file = Path(input_file).resolve()
    reference_dir = Path(reference_dir).resolve()

    if not project_path.is_dir():
        raise RuntimeError("Katalog projektu nie istnieje.")

    if not input_file.is_file():
        raise RuntimeError("Nie znaleziono pliku wejściowego.")

    # Zabezpieczenie: plik wejściowy musi leżeć w projekcie.
    if input_file.parent != project_path:
        raise RuntimeError(
            "Plik wejściowy musi znajdować się bezpośrednio "
            "w katalogu projektu."
        )

    params = get_parameters(parameters)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    final_output = project_path / f"face_blur_{timestamp}.mp4"
    temp_output = project_path / f"face_blur_temp_{timestamp}.mp4"

    cap = cv2.VideoCapture(str(input_file))

    if not cap.isOpened():
        raise RuntimeError("Nie można otworzyć pliku wideo.")

    out = None
    start_time = time.time()

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0:
            fps = 25.0

        if width <= 0 or height <= 0:
            raise RuntimeError(
                "Nie udało się odczytać rozdzielczości filmu."
            )

        # --------------------------------------------------
        # Model i referencje
        # --------------------------------------------------

        analyzer, providers = create_face_analyzer(params)

        references = load_reference_embeddings(
            analyzer,
            reference_dir,
        )

        # --------------------------------------------------
        # Zapis klatek do pliku tymczasowego
        # --------------------------------------------------

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        out = cv2.VideoWriter(
            str(temp_output),
            fourcc,
            fps,
            (width, height),
        )

        if not out.isOpened():
            raise RuntimeError(
                "Nie można utworzyć pliku tymczasowego wideo."
            )

        frame_index = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            frame_index += 1

            face_results = process_faces(
                analyzer,
                frame,
                references,
                params["recognition_threshold"],
            )

            for result in face_results:
                # Dopasowana osoba zostaje bez rozmycia.
                if result["matched"]:
                    continue

                x1, y1, x2, y2 = result["bbox"]

                blur_face(
                    frame,
                    x1,
                    y1,
                    x2,
                    y2,
                    params["blur_padding"],
                    params["blur_kernel"],
                )

            out.write(frame)

            if (
                progress_callback is not None
                and (
                    frame_index % 10 == 0
                    or frame_index == total_frames
                )
            ):
                progress_callback(frame_index, total_frames)

    finally:
        cap.release()

        if out is not None:
            out.release()

    # ------------------------------------------------------
    # Konwersja do H.264
    # ------------------------------------------------------

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        temp_output.unlink(missing_ok=True)
        raise RuntimeError(
            "Nie znaleziono FFmpeg w PATH. "
            "Zainstaluj FFmpeg lub dodaj go do zmiennej PATH."
        )

    command = [
        ffmpeg_path,
        "-y",
        "-i", str(temp_output),
        "-an",
        "-c:v", "libx264",
        "-preset", params["ffmpeg_preset"],
        "-crf", str(params["ffmpeg_crf"]),
        "-pix_fmt", "yuv420p",
        str(final_output),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Błąd podczas kodowania FFmpeg:\n"
                f"{result.stderr[-4000:]}"
            )

        if not final_output.exists() or final_output.stat().st_size == 0:
            raise RuntimeError(
                "FFmpeg nie utworzył prawidłowego pliku wynikowego."
            )

    finally:
        temp_output.unlink(missing_ok=True)

    elapsed = time.time() - start_time

    print(f"[FACE BLUR] Providers: {providers}")
    print(f"[FACE BLUR] Det size: {params['det_size']}")
    print(f"[FACE BLUR] Frames: {frame_index}")
    print(f"[FACE BLUR] Elapsed: {elapsed:.1f} s")
    print(f"[FACE BLUR] Output: {final_output.name}")

    return final_output