"""Filesystem and safe atomic I/O utilities for Harness 9."""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists and return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def resolve_path(path: Union[str, Path], base: Optional[Union[str, Path]] = None) -> Path:
    """Resolve path relative to base directory (or current working directory)."""
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    base_dir = Path(base) if base else Path.cwd()
    return (base_dir / p).resolve()


def atomic_write(
    file_path: Union[str, Path],
    content: Union[str, bytes],
    mode: str = "w",
    encoding: str = "utf-8",
) -> Path:
    """Atomically write content to file_path using a temporary replacement file."""
    target = Path(file_path).resolve()
    ensure_dir(target.parent)

    is_binary = "b" in mode or isinstance(content, bytes)
    write_mode = "wb" if is_binary else "w"

    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".tmp_{target.stem}_",
        suffix=target.suffix,
    )
    try:
        if is_binary:
            with os.fdopen(fd, write_mode) as f:
                if isinstance(content, str):
                    f.write(content.encode(encoding))
                else:
                    f.write(content)
        else:
            with os.fdopen(fd, write_mode, encoding=encoding) as f:
                f.write(content)  # type: ignore

        # Atomically replace target file
        os.replace(tmp_name, str(target))
    except Exception:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass
        raise

    return target


def save_json(
    file_path: Union[str, Path],
    data: Any,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> Path:
    """Save serializable data to JSON file with atomic write."""
    json_str = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    return atomic_write(file_path, json_str, mode="w", encoding="utf-8")


def load_json(file_path: Union[str, Path]) -> Any:
    """Load data from a JSON file."""
    target = Path(file_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"JSON file not found: {target}")
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def save_yaml(
    file_path: Union[str, Path],
    data: Any,
    sort_keys: bool = False,
) -> Path:
    """Save serializable data to YAML file with atomic write."""
    yaml_str = yaml.safe_dump(
        data,
        sort_keys=sort_keys,
        allow_unicode=True,
        default_flow_style=False,
    )
    return atomic_write(file_path, yaml_str, mode="w", encoding="utf-8")


def load_yaml(file_path: Union[str, Path]) -> Any:
    """Load data from a YAML file."""
    target = Path(file_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"YAML file not found: {target}")
    with open(target, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_text(file_path: Union[str, Path], text: str, encoding: str = "utf-8") -> Path:
    """Save string text to file atomically."""
    return atomic_write(file_path, text, mode="w", encoding=encoding)


def load_text(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Load text string from file."""
    target = Path(file_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"Text file not found: {target}")
    with open(target, "r", encoding=encoding) as f:
        return f.read()


def sha256_file(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hexadecimal checksum of a file on disk."""
    target = Path(file_path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"File not found for sha256: {target}")
    h = hashlib.sha256()
    with open(target, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hexadecimal checksum of raw bytes."""
    return hashlib.sha256(data).hexdigest()
