# Contributing

Thanks for considering a contribution.

## Local setup

```bash
python -m pip install -e .[dev]
```

## Before opening a PR

```bash
ruff check .
pytest
```

## What makes a good contribution

- New language detectors with tests.
- Better false-positive reduction.
- Faster scanning on large repos.
- Better docs and CI examples.
