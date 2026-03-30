import os
import re
import hashlib
from pathlib import Path
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent
STORAGE_ROOT = BASE_DIR / "storage"
EMPRESAS_DIR = STORAGE_ROOT / "empresas"
VIGILADORES_DIR = STORAGE_ROOT / "vigiladores"
BIBLIOTECA_DIR = STORAGE_ROOT / "biblioteca"
BIBLIOTECA_NORMAS_DIR = BIBLIOTECA_DIR / "normas"
BIBLIOTECA_DOCUMENTOS_DIR = BIBLIOTECA_DIR / "documentos"

ALLOWED_EXTENSIONS = {".pdf"}
ALLOWED_MIME_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def ensure_storage_dirs() -> None:
    for path in (
        STORAGE_ROOT,
        EMPRESAS_DIR,
        VIGILADORES_DIR,
        BIBLIOTECA_DIR,
        BIBLIOTECA_NORMAS_DIR,
        BIBLIOTECA_DOCUMENTOS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    base_name = Path(filename).name.strip()
    stem = Path(base_name).stem
    extension = Path(base_name).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "documento"
    return f"{safe_stem}{extension}"


def validate_pdf_metadata(filename: str, mime_type: str | None = None, size_bytes: int | None = None) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Solo se permiten archivos PDF")

    if mime_type and mime_type.lower() not in ALLOWED_MIME_TYPES:
        raise ValueError("El tipo MIME del archivo no corresponde a un PDF valido")

    if size_bytes is not None and size_bytes > MAX_FILE_SIZE_BYTES:
        raise ValueError("El archivo excede el tamano maximo permitido de 10 MB")


def entity_storage_dir(entity_type: str, entity_id: int) -> Path:
    if entity_type == "empresa":
        return EMPRESAS_DIR / str(entity_id)
    if entity_type == "vigilador":
        return VIGILADORES_DIR / str(entity_id)
    raise ValueError("entity_type debe ser 'empresa' o 'vigilador'")


def build_document_path(entity_type: str, entity_id: int, original_filename: str) -> str:
    ensure_storage_dirs()
    safe_name = sanitize_filename(original_filename)
    extension = Path(safe_name).suffix.lower()
    unique_name = f"{entity_type}_{entity_id}_{uuid4().hex}{extension}"
    target_dir = entity_storage_dir(entity_type, entity_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    return os.fspath(target_dir / unique_name)


def build_library_document_path(category: str, original_filename: str) -> str:
    ensure_storage_dirs()
    safe_name = sanitize_filename(original_filename)
    extension = Path(safe_name).suffix.lower()
    category_key = (category or "").strip().lower()
    if category_key == "normativa":
        target_dir = BIBLIOTECA_NORMAS_DIR
        prefix = "norma"
    else:
        target_dir = BIBLIOTECA_DOCUMENTOS_DIR
        prefix = "biblioteca"
    target_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{prefix}_{uuid4().hex}{extension}"
    return os.fspath(target_dir / unique_name)


def compute_file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
