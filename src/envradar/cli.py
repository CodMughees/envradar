from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import load_scan_config
from .render import render_report, write_docs_markdown, write_env_example
from .scanner import scan_repo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envradar",
        description="Detect undocumented, unused, and drifting environment variables in a repository.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Path to the repository to scan.")
    parser.add_argument(
        "--format",
        choices=("text", "markdown", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument("--config", help="Optional path to envradar.yml.")
    parser.add_argument(
        "--write-example",
        metavar="PATH",
        help="Write a generated .env.example-style file to PATH.",
    )
    parser.add_argument(
        "--write-docs",
        metavar="PATH",
        help="Write a markdown environment reference to PATH.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when missing, stale, or undocumented local variables are found.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def resolve_output_path(root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    return candidate if candidate.is_absolute() else root / candidate


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.exists():
        parser.error(f"Path does not exist: {root}")
    if not root.is_dir():
        parser.error(f"Path must be a directory: {root}")

    try:
        config, _ = load_scan_config(root, args.config)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    result = scan_repo(root, config=config)
    print(render_report(result, args.format), end="")

    if args.write_example:
        example_path = resolve_output_path(root, args.write_example)
        write_env_example(result, example_path)
        print(f"Wrote {example_path}", file=sys.stderr)

    if args.write_docs:
        docs_path = resolve_output_path(root, args.write_docs)
        write_docs_markdown(result, docs_path)
        print(f"Wrote {docs_path}", file=sys.stderr)

    if args.strict and result.strict_findings:
        return 1
    return 0
