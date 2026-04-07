from __future__ import annotations

import os
import re
from pathlib import Path

from .models import ScanConfig, ScanResult

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".turbo",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}

MAX_FILE_SIZE = 1_000_000

CODE_SUFFIXES = {
    ".cjs",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".ts",
    ".tsx",
}

CODE_PATTERNS = [
    re.compile(r"process\.env\.([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r'process\.env\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r"import\.meta\.env\.([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r'Deno\.env\.get\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\)'),
    re.compile(r'os\.environ\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'os\.environ\.get\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'os\.getenv\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'ENV\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'ENV\.fetch\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'os\.Getenv\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\)'),
    re.compile(r'os\.LookupEnv\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\)'),
    re.compile(r'System\.getenv\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\)'),
    re.compile(r'Environment\.GetEnvironmentVariable\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\)'),
    re.compile(r'std::env::var(?:_os)?\(\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\)'),
    re.compile(r'getenv\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\)'),
]

ENV_ASSIGNMENT_PATTERN = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
PLACEHOLDER_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::?[-?][^}]*)?}")
WORKFLOW_SECRET_PATTERN = re.compile(r"\$\{\{\s*secrets\.([A-Za-z_][A-Za-z0-9_]*)\s*}}")
WORKFLOW_VAR_PATTERN = re.compile(r"\$\{\{\s*vars\.([A-Za-z_][A-Za-z0-9_]*)\s*}}")

DOCUMENTED_ENV_MARKERS = ("example", "sample", "template")
COMPOSE_FILENAMES = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}


def scan_repo(root: str | Path, config: ScanConfig | None = None) -> ScanResult:
    repo_root = Path(root).resolve()
    result = ScanResult(root=repo_root, config=config or ScanConfig())

    for path in iter_repo_files(repo_root):
        if is_binary_file(path):
            continue
        relative = path.relative_to(repo_root).as_posix()
        result.scanned_files += 1

        role = env_file_role(path.name)
        if role is not None:
            parse_env_file(path, relative, role, result)
        if is_compose_file(path):
            parse_compose_file(path, relative, result)
        if is_workflow_file(path):
            parse_workflow_file(path, relative, result)
        if is_code_file(path):
            parse_code_file(path, relative, result)

    return result


def iter_repo_files(root: Path):
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [directory for directory in dirs if directory not in IGNORED_DIRS]
        for filename in files:
            path = Path(current_root) / filename
            try:
                if path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue
            yield path


def is_binary_file(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:1024]
    except OSError:
        return True
    return b"\x00" in chunk


def is_code_file(path: Path) -> bool:
    return path.suffix.lower() in CODE_SUFFIXES


def is_workflow_file(path: Path) -> bool:
    if path.suffix.lower() not in {".yml", ".yaml"}:
        return False
    parts = path.parts
    return len(parts) >= 3 and parts[-3] == ".github" and parts[-2] == "workflows"


def is_compose_file(path: Path) -> bool:
    return path.name.lower() in COMPOSE_FILENAMES


def env_file_role(filename: str) -> str | None:
    lowered = filename.lower()
    if not lowered.startswith(".env") and not lowered.endswith(".env"):
        return None
    if any(marker in lowered for marker in DOCUMENTED_ENV_MARKERS):
        return "documented"
    return "local"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_code_file(path: Path, relative: str, result: ScanResult) -> None:
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        for pattern in CODE_PATTERNS:
            for match in pattern.finditer(line):
                result.add("code", match.group(1), relative, line_number)


def parse_compose_file(path: Path, relative: str, result: ScanResult) -> None:
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        for name in PLACEHOLDER_PATTERN.findall(line):
            result.add("compose", name, relative, line_number)


def parse_workflow_file(path: Path, relative: str, result: ScanResult) -> None:
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        for name in WORKFLOW_SECRET_PATTERN.findall(line):
            result.add("workflow_secrets", name, relative, line_number)
        for name in WORKFLOW_VAR_PATTERN.findall(line):
            result.add("workflow_vars", name, relative, line_number)


def parse_env_file(path: Path, relative: str, role: str, result: ScanResult) -> None:
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = ENV_ASSIGNMENT_PATTERN.match(line)
        if not match:
            continue
        name, raw_value = match.groups()
        if role == "documented":
            result.add("documented", name, relative, line_number, value=raw_value.strip())
        else:
            result.add("local", name, relative, line_number)
