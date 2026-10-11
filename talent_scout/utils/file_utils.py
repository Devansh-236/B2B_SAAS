import json
import os
import re

_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")
PDF_MAGIC = b"%PDF-"


def is_valid_identifier(value) -> bool:
    """Allow only short, filesystem-safe identifiers (letters, digits, '_' and '-')."""
    return isinstance(value, str) and _IDENTIFIER_RE.fullmatch(value) is not None


def is_pdf_bytes(content: bytes) -> bool:
    return content.startswith(PDF_MAGIC)


def safe_join(base_dir: str, *parts: str) -> str:
    """Join paths under base_dir and ensure the result stays inside it."""
    base = os.path.realpath(base_dir)
    path = os.path.realpath(os.path.join(base, *parts))
    if os.path.commonpath([base, path]) != base:
        raise ValueError("Resolved path escapes the data directory.")
    return path


def save_bytes(content: bytes, destination: str) -> None:
    with open(destination, "wb") as buffer:
        buffer.write(content)


def write_json_atomic(data: dict, destination: str) -> None:
    """Write JSON to a temp file and rename it, so readers never see partial files."""
    tmp_path = destination + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, destination)
