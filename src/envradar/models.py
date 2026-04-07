from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, order=True)
class Location:
    path: str
    line: int

    def display(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass
class ScanConfig:
    ignore: set[str] = field(default_factory=set)
    placeholders: dict[str, str] = field(default_factory=dict)


@dataclass
class ScanResult:
    root: Path
    config: ScanConfig
    scanned_files: int = 0
    code: dict[str, set[Location]] = field(default_factory=dict)
    documented: dict[str, set[Location]] = field(default_factory=dict)
    compose: dict[str, set[Location]] = field(default_factory=dict)
    workflow_secrets: dict[str, set[Location]] = field(default_factory=dict)
    workflow_vars: dict[str, set[Location]] = field(default_factory=dict)
    local: dict[str, set[Location]] = field(default_factory=dict)
    example_values: dict[str, str] = field(default_factory=dict)

    def add(self, category: str, name: str, path: str, line: int, value: str | None = None) -> None:
        cleaned = name.strip()
        if not cleaned or cleaned in self.config.ignore:
            return
        bucket: dict[str, set[Location]] = getattr(self, category)
        bucket.setdefault(cleaned, set()).add(Location(path=path, line=line))
        if category == "documented" and value is not None and cleaned not in self.example_values:
            self.example_values[cleaned] = value

    def keys_for(self, category: str) -> set[str]:
        return set(getattr(self, category).keys())

    @property
    def required_runtime(self) -> set[str]:
        return self.keys_for("code") | self.keys_for("compose")

    @property
    def missing_from_examples(self) -> list[str]:
        return sorted(self.required_runtime - self.keys_for("documented"))

    @property
    def unused_in_examples(self) -> list[str]:
        return sorted(self.keys_for("documented") - self.required_runtime)

    @property
    def local_only(self) -> list[str]:
        return sorted(self.keys_for("local") - self.keys_for("documented"))

    @property
    def workflow_only(self) -> list[str]:
        return sorted(
            (self.keys_for("workflow_secrets") | self.keys_for("workflow_vars"))
            - self.required_runtime
            - self.keys_for("documented")
        )

    @property
    def all_variables(self) -> list[str]:
        return sorted(
            self.required_runtime
            | self.keys_for("documented")
            | self.keys_for("local")
            | self.keys_for("workflow_secrets")
            | self.keys_for("workflow_vars")
        )

    @property
    def strict_findings(self) -> int:
        return len(self.missing_from_examples) + len(self.unused_in_examples) + len(self.local_only)

    def locations_for(self, category: str, name: str) -> list[Location]:
        return sorted(getattr(self, category).get(name, set()))

    def all_locations_for(self, name: str) -> list[Location]:
        combined: set[Location] = set()
        for category in ("code", "documented", "compose", "workflow_secrets", "workflow_vars", "local"):
            combined |= set(getattr(self, category).get(name, set()))
        return sorted(combined)

    def to_dict(self) -> dict:
        variables: dict[str, dict[str, list[str]]] = {}
        for name in self.all_variables:
            variables[name] = {
                "code": [loc.display() for loc in self.locations_for("code", name)],
                "documented": [loc.display() for loc in self.locations_for("documented", name)],
                "local": [loc.display() for loc in self.locations_for("local", name)],
                "compose": [loc.display() for loc in self.locations_for("compose", name)],
                "workflow_secrets": [loc.display() for loc in self.locations_for("workflow_secrets", name)],
                "workflow_vars": [loc.display() for loc in self.locations_for("workflow_vars", name)],
            }
        return {
            "summary": {
                "scanned_files": self.scanned_files,
                "required_runtime_vars": len(self.required_runtime),
                "documented_vars": len(self.keys_for("documented")),
                "local_vars": len(self.keys_for("local")),
                "workflow_vars": len(self.keys_for("workflow_secrets") | self.keys_for("workflow_vars")),
                "strict_findings": self.strict_findings,
            },
            "findings": {
                "missing_from_examples": self.missing_from_examples,
                "unused_in_examples": self.unused_in_examples,
                "local_only": self.local_only,
                "workflow_only": self.workflow_only,
            },
            "variables": variables,
        }
