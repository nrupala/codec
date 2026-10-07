# Contributing to CodeC

## How changes land (PR-flow)

1. Create a branch from `main` for each workstream (`feat/...`, `fix/...`, `chore/...`).
2. Open a **draft PR** early; mark it ready for review when tests are green.
3. The owner (Nrupal Akolkar) merges. **No direct pushes to `main` — ever.**
   (Until branch protection with required checks is enabled, this is manual discipline — say so plainly, and say it again in the PR.)
4. Each PR adds its entry under `## [Unreleased]` in `CHANGELOG.md`.
5. Version bumps follow SemVer (patch = fix, minor = feature, major = breaking).
   This repo currently has no version file — if one is introduced, follow the rule above.
6. Merge commits reference the PR number; releases are tagged `vX.Y.Z` after merge.

## Build / test

```bash
pip install -r requirements.txt

# All tests (77: 46 basic + 31 advanced)
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=codec

# Single test file
python -m pytest tests/test_advanced.py -v
```

See `docs/development.md` for the project structure and how to add a new tool
(use the `@register_tool` decorator) or a new LLM backend.

## License

> ⚠️ README states MIT, but no `LICENSE` file is present in this repository
> (flagged for the owner). Do not add license headers until that is resolved.
