# envradar

Find undocumented, unused, and drifting environment variables before they confuse the next person who clones your repo.

envradar scans source code, `.env` files, Docker Compose files, and GitHub Actions workflows to answer four annoying questions quickly:

- Which variables are used in code but missing from `.env.example`?
- Which variables are documented but no longer used?
- Which variables exist locally but are not documented for new contributors?
- Which secrets only show up in CI pipelines and deserve a second look?

It is designed to be fast, safe, and CI-friendly:

- Read-only by default.
- Never prints local `.env` values.
- Works well in pre-release checks for open-source repos.
- Can generate a fresh `.env.example` and a markdown environment reference.

## Why this is useful

Environment variable drift is one of the most common sources of bad onboarding, broken preview deploys, and “works on my machine” bugs. envradar gives maintainers a low-friction way to catch that drift before publishing a repo or merging a pull request.

## Features

- Detects env vars in Python, JavaScript, TypeScript, Go, Ruby, Java, Kotlin, Rust, PHP, and .NET-style code.
- Parses `.env.example`, `.env.sample`, `.env.template`, and local `.env*` files.
- Detects `${VAR}` placeholders in Docker Compose files.
- Detects `${{ secrets.NAME }}` and `${{ vars.NAME }}` references in GitHub Actions workflows.
- Outputs plain text, markdown, or JSON.
- Supports a small `envradar.yml` config for ignored variables and placeholder values.
- Exits non-zero in `--strict` mode so you can use it in CI.

## Install from source

```bash
python -m pip install -e .
```

Or with `pipx`:

```bash
pipx install .
```

## Quick start

Scan the current repository:

```bash
envradar .
```

Get copy-pasteable markdown output:

```bash
envradar . --format markdown
```

Fail CI when drift is found:

```bash
envradar . --strict
```

Generate a fresh `.env.example`:

```bash
envradar . --write-example .env.example
```

Generate a docs page for contributors:

```bash
envradar . --write-docs docs/environment.md
```

## Example output

```text
$ envradar .

envradar scanned 42 files.
Required runtime vars: 3
Documented vars: 2

Missing from .env.example (1)
  - DATABASE_URL -- src/settings.py:12, docker-compose.yml:8

Documented but not used (1)
  - SENTRY_DSN -- .env.example:7

Present locally but not documented (1)
  - STRIPE_WEBHOOK_SECRET -- .env:4

Workflow-only secrets or vars (1)
  - PYPI_API_TOKEN -- .github/workflows/release.yml:22
```

## Config

If `envradar.yml` or `.envradar.yml` exists at the repo root, envradar will load it automatically.

```yaml
ignore:
  - CI
  - GITHUB_TOKEN
  - PYPI_API_TOKEN

placeholders:
  DATABASE_URL: postgresql://localhost:5432/app
  REDIS_URL: redis://localhost:6379/0
```

`ignore` removes noisy variables from every report. `placeholders` are used when generating `.env.example`.

## JSON output

```bash
envradar . --format json
```

This is useful for automation, bots, or dashboards.

## GitHub Actions example

```yaml
name: envradar
on:
  pull_request:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -e .
      - run: envradar . --strict
```

## Safety notes

- envradar never prints values from local `.env` files.
- Generated `.env.example` files only reuse values already present in example/template files or explicit placeholders from config.
- Real secrets stay local unless you intentionally type them into tracked example files yourself.

## Limitations

- The scanner relies on static patterns, so deeply dynamic env lookups may be missed.
- Monorepos with many independent apps may want separate runs per package.
- Shell scripts are intentionally not parsed yet to avoid too many false positives.

## Development

```bash
python -m pip install -e .[dev]
ruff check .
pytest
```

## License

MIT
