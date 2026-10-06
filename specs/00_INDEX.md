# AI Game Lab Fighter — Spec Index (00_INDEX)

> **Entry point for any human or LLM agent working on this repository.** Read this
> file first, then the specs in the recommended order below.

## What this project is

AI Game Lab is an educational, multi-user **Flask** web application. Students configure
an **AI taekwondo fighter** (an LLM "brain" + 7 athlete attributes "body") and watch two
fighters resolve a fight driven by a deterministic "core" (rules + combat). The move set
and sprites are adapted from the open-source 2D game `alinikan/StreetFighter`.

The whole teaching idea is the **brain / body / core** separation: the LLM decides
tactics, the deterministic body executes, the deterministic core scores — so every
exchange is explainable and reproducible.

## Tech stack & commands

| Area | Value |
| --- | --- |
| Language | Python 3.10+ (developed on 3.14) |
| Web | Flask, SQLAlchemy, Alembic, Flask-Login, Jinja2 + HTMX + vanilla JS |
| DB / queue | PostgreSQL, Redis (rq) |
| LLM | multi-provider OpenAI-compatible (`LLM_PROVIDERS` env), offline `mock` fallback |
| Domain | `app/domain/taekwondo/` (brain / body / core + engine + events) |
| Run | `flask --app run.py run` |
| Test | `pytest` |
| Migrate | `flask --app run.py db upgrade` |
| Seed | `flask --app run.py seed` |

## Recommended reading order

1. `README.md` — project overview, goals, quick start.
2. `FIGHTER_SPEC.md` — **the authoritative game spec**: arena, rounds, exchanges, the
   7 attributes, point-buy, archetypes, strategies, decision protocol, combat.
3. `AGENT_ARCHITECTURE.md` — brain / body / core, tools vs skills, the agent files.
4. `ARCHITECTURE.md` — layers, boundaries, the interaction loop, and the **event
   contract** (exact payload shapes).
5. `DATA_MODEL.md` — DB entities and JSON shapes.
6. `PROMPT_ARCHITECTURE.md` + `DEFAULT_PROMPTS.md` — how the LLM prompt is built.
7. `EDUCATIONAL_MODEL.md` — pedagogy.
8. `CODING_AGENT_PROMPT.md` — implementation guidance for a coding agent.
9. `SECURITY_AND_SANDBOX.md` — sandbox and authorization rules.
10. `FOLDER_STRUCTURE.md` — repository layout.

## Specs (one-line purpose)

| File | Purpose |
| --- | --- |
| `00_INDEX.md` | This index + reading order. |
| `manifest.yaml` | Machine-readable project metadata (stack, commands, spec list). |
| `README.md` | Overview, goals, quick start, configuration, license. |
| `FIGHTER_SPEC.md` | Full taekwondo game rules, combat, attributes, economy. |
| `AGENT_ARCHITECTURE.md` | Brain / body / core model and the agent files. |
| `ARCHITECTURE.md` | Application layers + **event contract** (payload shapes). |
| `DATA_MODEL.md` | DB schema + configuration JSON shapes. |
| `PROMPT_ARCHITECTURE.md` | Prompt layers and the output protocol. |
| `DEFAULT_PROMPTS.md` | Prompt templates + strategy presets. |
| `EDUCATIONAL_MODEL.md` | Learning goals and progression. |
| `CODING_AGENT_PROMPT.md` | Instructions for a coding agent implementing/editing this app. |
| `SECURITY_AND_SANDBOX.md` | No-arbitrary-execution rules, authorization, secrets. |
| `FOLDER_STRUCTURE.md` | Directory layout. |

## For LLM agents (how to operate this repo)

- **Start here** (this file), then `manifest.yaml` (stack/commands), then
  `FIGHTER_SPEC.md` (the game) and `ARCHITECTURE.md` (§ event contract).
- **To verify any change:** run `pytest` from `AI-Edu-game-lab-app-v1/`. A green suite
  is the minimum bar before committing.
- **Do not break the event contract:** the JS simulator (`app/web/static/js/sim/`) reads
  state fields at `payload.<field>` (e.g. `payload.rounds_won`, `payload.positions`,
  `payload.winner`). State-carrying events MUST be emitted flat (see `engine.py`
  `_state_payload`), never nested under a second `payload`.
- **Domain is Flask-free** (`app/domain/taekwondo/`); routes call services, services call
  the domain. The graphical sim is an independent module driven only by the event stream.
