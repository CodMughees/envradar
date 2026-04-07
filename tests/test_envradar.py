from __future__ import annotations

from pathlib import Path

from envradar.models import ScanConfig
from envradar.render import write_docs_markdown, write_env_example
from envradar.scanner import scan_repo


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_detects_missing_and_stale_variables(tmp_path: Path) -> None:
    write(
        tmp_path / "src/app.py",
        """import os
DATABASE_URL = os.getenv("DATABASE_URL")
""",
    )
    write(
        tmp_path / "web.ts",
        """const api = process.env.API_TOKEN
""",
    )
    write(
        tmp_path / ".env.example",
        """API_TOKEN=demo
STALE_VALUE=1
""",
    )

    result = scan_repo(tmp_path, config=ScanConfig())

    assert result.missing_from_examples == ["DATABASE_URL"]
    assert result.unused_in_examples == ["STALE_VALUE"]
    assert sorted(result.required_runtime) == ["API_TOKEN", "DATABASE_URL"]


def test_does_not_copy_local_secret_values_into_generated_example(tmp_path: Path) -> None:
    write(
        tmp_path / "service.py",
        """import os
SECRET_KEY = os.getenv("SECRET_KEY")
""",
    )
    write(
        tmp_path / ".env",
        """SECRET_KEY=super-secret-value
""",
    )

    result = scan_repo(tmp_path, config=ScanConfig())
    output = tmp_path / ".env.example"
    write_env_example(result, output)
    generated = output.read_text(encoding="utf-8")

    assert "SECRET_KEY=" in generated
    assert "super-secret-value" not in generated


def test_compose_and_workflow_detection(tmp_path: Path) -> None:
    write(
        tmp_path / "docker-compose.yml",
        """services:
  app:
    environment:
      DATABASE_URL: ${DATABASE_URL}
""",
    )
    write(
        tmp_path / ".github/workflows/release.yml",
        """jobs:
  publish:
    steps:
      - run: echo "${{ secrets.PYPI_API_TOKEN }}"
""",
    )

    result = scan_repo(tmp_path, config=ScanConfig())

    assert result.missing_from_examples == ["DATABASE_URL"]
    assert result.workflow_only == ["PYPI_API_TOKEN"]


def test_writes_markdown_docs(tmp_path: Path) -> None:
    write(
        tmp_path / "src/settings.py",
        """import os
LOG_LEVEL = os.getenv("LOG_LEVEL")
""",
    )
    write(
        tmp_path / ".env.example",
        """LOG_LEVEL=info
""",
    )

    result = scan_repo(tmp_path, config=ScanConfig())
    docs_path = tmp_path / "docs/environment.md"
    write_docs_markdown(result, docs_path)

    content = docs_path.read_text(encoding="utf-8")
    assert "# Environment variables" in content
    assert "| LOG_LEVEL | yes | yes | no | no | no |" in content
