from __future__ import annotations

from pathlib import Path

import yaml

from .models import ScanConfig

DEFAULT_IGNORE = {
    "CI",
    "GITHUB_ACTION",
    "GITHUB_ACTIONS",
    "GITHUB_ACTOR",
    "GITHUB_REF",
    "GITHUB_REPOSITORY",
    "GITHUB_SHA",
    "GITHUB_TOKEN",
    "HOME",
    "PATH",
    "PWD",
    "RUNNER_ARCH",
    "RUNNER_OS",
    "RUNNER_TEMP",
    "RUNNER_TOOL_CACHE",
    "SHELL",
    "TMPDIR",
    "USER",
}

CONFIG_FILENAMES = ("envradar.yml", ".envradar.yml")


def load_scan_config(root: Path, explicit_path: str | None = None) -> tuple[ScanConfig, Path | None]:
    candidate: Path | None = None
    if explicit_path:
        path = Path(explicit_path)
        candidate = path if path.is_absolute() else root / path
        if not candidate.exists():
            raise FileNotFoundError(f"Config file not found: {candidate}")
    else:
        for name in CONFIG_FILENAMES:
            maybe = root / name
            if maybe.exists():
                candidate = maybe
                break

    if candidate is None:
        return ScanConfig(ignore=set(DEFAULT_IGNORE), placeholders={}), None

    raw = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    ignore = set(DEFAULT_IGNORE)
    for item in raw.get("ignore", []) or []:
        cleaned = str(item).strip()
        if cleaned:
            ignore.add(cleaned)

    placeholders = {
        str(key).strip(): str(value)
        for key, value in (raw.get("placeholders", {}) or {}).items()
        if str(key).strip()
    }
    return ScanConfig(ignore=ignore, placeholders=placeholders), candidate
