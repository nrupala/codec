# Test plan — codec (CodeC)

## Scope

The pytest suite under `tests/` covers CodeC's core modules and tools:
the prompt engineer, resource allocator, task decomposer, scheduler,
action definer, state manager, and module logger; the tool registry and
the file-operations and search tools; the session guardian and session
memory; and the OS and code bridges. Live calls to external LLM backends
are out of scope — the suite exercises the local modules, tools, and
session machinery.

## Suites

| Suite | Covers | Run it | Runs in CI |
|---|---|---|---|
| pytest — `tests/test_basic.py` (46 tests) | Core modules, tool registry, file/search tools, session guardian/memory, OS/code bridges | `python -m pytest tests/` | Yes — `.github/workflows/tests.yml` |
| pytest — `tests/test_advanced.py` (31 tests) | Advanced module and tool behaviour | `python -m pytest tests/` | Yes — `.github/workflows/tests.yml` |

## CI gates

- Full pytest suite green on every push and pull request to `main`
  (`.github/workflows/tests.yml`, Python 3.12, dependencies from
  `requirements.txt` plus `pytest` and `pytest-asyncio` — the suite's
  async tests carry `@pytest.mark.asyncio` — run as `pytest -q`).
- CodeQL static analysis on push, pull request, and weekly
  (`.github/workflows/codeql.yml`).
- Per CONTRIBUTING.md: pull requests are marked ready for review when
  tests are green.

## Cadence

- Every pull request: the full pytest suite (Tests workflow) and CodeQL.
- Every push to `main`: the full pytest suite and CodeQL.
- Weekly: CodeQL on its schedule.
- Every release candidate: the release-readiness run (checker + evidence
  reads), per the house Release-Readiness Standard.

## Coverage bar

No numeric floor; new functionality lands with tests per CONTRIBUTING.md.
