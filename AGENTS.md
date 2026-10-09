DO not make changes until you have 95% confidence in what you need to build, ask me followup until you reach the confidence

# Development Guidelines for Codex

> **About this file (v3.0.0-py):** Lean version optimized for context efficiency. Core principles here; detailed patterns loaded on-demand via skills.
>
> **Adapted for this project:** the upstream v3.0.0 guidelines are TypeScript/Vitest-oriented. This project is pure Python (Flask + Swiss Ephemeris + pytest), so the tooling references below are translated. The philosophy — TDD, behavior-driven testing, functional style, small increments — is unchanged.

## Project Context

Jain Panchang is a sunrise-based Panchang generator: a Flask web app plus CLI over Swiss Ephemeris, with Jain festival rules for three Shwetambar profiles.

- **Source root:** `python_engine/` (nested one level below the repo root)
- **Environment:** `python_engine/.venv-win` (Python 3.14). `pyswisseph` has no cp314 wheel — see `docs/setup_and_usage.md`.
- **Tests:** `pytest tests` and `pytest tests_ui` must be run separately.
- **Docs:** `docs/` is long-form and kept accurate; `plans/` holds design docs for in-flight work.
- **Client release:** `python scripts/build_client_bundle.py` writes the gitignored `client_release/` + zip at the repo root (Windows, `start.bat`, Python 3.11–3.14 with bundled wheels). Launcher files live in `client_files/`; see `docs/setup_and_usage.md` §10c.

## Core Philosophy

**TEST-DRIVEN DEVELOPMENT IS NON-NEGOTIABLE.** Every single line of production code must be written in response to a failing test. No exceptions. This is not a suggestion or a preference — it is the fundamental practice that enables all other principles in this document.

I follow Test-Driven Development (TDD) with a strong emphasis on behavior-driven testing and functional programming principles. All work should be done in small, incremental changes that maintain a working state throughout development.

## Quick Reference

**Key Principles:**

- Write tests first (TDD)
- Test behavior, not implementation
- Type hints on public functions; no bare `Any` where a real type exists
- Immutable data only
- Small, pure functions
- Use real domain types in tests, never redefine them

**Preferred Tools:**

- **Language**: Python 3.14, `from __future__ import annotations`, PEP 604 unions
- **Testing**: pytest (+ `pytest-subtests`); Playwright for `tests_ui`
- **State Management**: frozen dataclasses, module-level constants

## Testing Principles

**Core principle**: Test behavior, not implementation. 100% coverage through business behavior.

**Quick reference:**
- Write tests first (TDD non-negotiable)
- Test through public API exclusively
- Use factory functions for test data (no module-level mutable fixtures)
- Tests must document expected business behavior
- No 1:1 mapping between test files and implementation files

Astronomical code has a specific trap: a test that hardcodes an ephemeris output is a change-detector, not a behavior test. Prefer asserting invariants (a Tithi index is 1–30; a window's end follows its start; a cached value equals the uncached one) over golden numbers. Where a golden date is genuinely the specification — a festival's canonical date — cite the source in the test.

For detailed testing patterns and examples, load the `testing` skill.
For verifying test effectiveness through mutation analysis, load the `mutation-testing` skill.

## Python Guidelines

**Core principle**: Explicit types at trust boundaries, plain types for internal logic.

**Quick reference:**
- Type-hint every public function signature
- No `Any` where a real type exists (use `object` if genuinely unknown)
- Prefer `@dataclass(frozen=True)` over dicts for structured data
- Validate at trust boundaries (`request_parsing.py`), trust internal calls
- Never `except Exception: pass` — if a failure is expected, name it and handle it; if it is not, let it raise

## Code Style

**Core principle**: Functional programming with immutable data. Self-documenting code.

**Quick reference:**
- No data mutation — immutable data structures only
- Pure functions wherever possible
- No nested if/else — use early returns or composition
- Comments explain *why*, never *what* — code should be self-documenting
- Prefer keyword arguments over positional parameters
- Use comprehensions and `itertools` over accumulator loops

Domain exception: this codebase's `panchang.py` and `astronomy.py` carry explanatory comments about the underlying astronomy and the classical rules. Those earn their place — a reader cannot derive "Panchak is Moon longitude 300°–360°" from the code. Keep them.

For detailed patterns and examples, load the `functional` skill.

## Development Workflow

**Core principle**: RED-GREEN-MUTATE-KILL MUTANTS-REFACTOR in small, known-good increments. TDD is the fundamental practice.

**Quick reference:**
- RED: Write failing test first (NO production code without failing test)
- GREEN: Write MINIMUM code to pass test
- MUTATE: Run mutation testing to verify test effectiveness, produce a report
- KILL MUTANTS: Address surviving mutants (ask human when value is ambiguous)
- REFACTOR: Assess improvement opportunities (only refactor if adds value)
- **Wait for commit approval** before every commit
- Each increment leaves codebase in working state

For detailed TDD workflow, load the `tdd` skill.
For refactoring methodology, load the `refactoring` skill.
For significant work, load the `planning` skill. Plans live in `plans/` directory.
For CI failure diagnosis, load the `ci-debugging` skill.

## Output Guardrails

- **Write to files, not chat** — When asked to produce a plan, document, or artifact, always persist it to a file. You may also present it inline for approval, but the file is the source of truth.
- **Plan-only mode** — When asked for a plan, design, or document only, produce ONLY that artifact. Do not write production code, test code, or make any implementation changes unless explicitly asked.
- **Incremental output** — When exploring a codebase, produce a first draft of output within 3-4 tool calls. Refine iteratively rather than front-loading all exploration before producing anything.

## Working with Codex

**Core principle**: Think deeply, follow TDD strictly, capture learnings while context is fresh.

**Quick reference:**
- ALWAYS FOLLOW TDD — no production code without failing test
- Assess refactoring after every green (but only if adds value)
- Update AGENTS.md when introducing meaningful changes
- Ask "What do I wish I'd known at the start?" after significant changes
- Document gotchas, patterns, decisions, edge cases while context is fresh

For detailed TDD workflow, load the `tdd` skill.
For refactoring methodology, load the `refactoring` skill.
For detailed guidance on expectations and documentation, load the `expectations` skill.

## Summary

The key is to write clean, testable, functional code that evolves through small, safe increments. Every change should be driven by a test that describes the desired behavior, and the implementation should be the simplest thing that makes that test pass. When in doubt, favor simplicity and readability over cleverness.
