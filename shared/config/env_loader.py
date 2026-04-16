"""Minimal .env loader for local Python entrypoints."""

from __future__ import annotations

import os
from pathlib import Path


def load_project_env(start_path: str | Path | None = None) -> Path | None:
    """Load a project-level .env file into process env when present.

    Existing environment variables win over values from the file.
    """

    search_root = Path(start_path or __file__).resolve()
    for candidate_root in [search_root, *search_root.parents]:
        env_path = candidate_root / ".env"
        if env_path.exists():
            _load_env_file(env_path)
            return env_path
    return None


def _load_env_file(env_path: Path) -> None:
    """Parse KEY=VALUE lines from a .env file."""

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
