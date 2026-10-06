# AI Game Lab — Fighter Spec (Taekwondo)

## Purpose

AI Game Lab is an educational, browser-based, multi-user platform for learning how large
language models work — by configuring **teams of AI agents** that play a **single,
deeply-simulated game: a taekwondo fight**.

The layered architecture, LLM multi-provider abstraction, multi-user matchmaking, and
interaction log are retained from the beach-volleyball version; the volleyball engine is
replaced by a **taekwondo fighting engine**. This version takes its move set and visual
assets (sprites, audio, background) as reference from the open-source 2D fighting game
[`alinikan/StreetFighter`](https://github.com/alinikan/StreetFighter).

The pedagogical core is the separation between an agent's **mind** (the LLM: model +
parameters, deciding tactics) and its **body** (7 athlete attributes: how well the body
executes). Students configure both, run a fight, and read the interaction log to
understand how each decision and each attribute shaped the result.

## What the platform exposes

- **Teams of 1 fighter** (no partner): each user configures a single taekwondo fighter.
- **7 athlete attributes** per fighter (Kick Speed, Kick Power, Precision, Defense,
  Agility, Stamina, Reach), set with 1–10 sliders.
- **Point-buy economy** with difficulty levels (Easy/Medium/Hard) and preset archetypes.
- **LLM model + model parameters** per fighter, each with a plain-language explanation.
- **Models chosen from a list** built from the `LLM_PROVIDERS` environment variable.
- **Multi-user fights**: invite an online player, each configures their fighter, both
  ready up, the fight auto-starts.
- **Interaction log**: prompt, model, parameters, raw + parsed decision, athlete
  attributes, and combat outcome for every exchange.
- **Graphical fight simulation**: an independent, self-contained animation module of the
  two fighters on a side-view arena.
- **Match history**: every fight persisted and browsable by teachers.

## Architecture

- Flask application, Jinja2 + HTMX + a small amount of JavaScript
- PostgreSQL for persistent data; Redis for the async queue + presence
- SQLAlchemy + Alembic; Flask-Login
- Multi-provider / multi-model LLM abstraction (`LLM_PROVIDERS` env)
- Taekwondo fighting domain engine (state, rules, stochastic combat, attributes)
- Event-based interaction log
- Multi-user matchmaking (1v1)
- Independent graphical simulation module
- User administration (admin)

## See also

- `FIGHTER_SPEC.md` — the complete fight mechanics, attribute schema, and economy.
- `ARCHITECTURE.md`, `DATA_MODEL.md`, `EDUCATIONAL_MODEL.md`, `CODING_AGENT_PROMPT.md`,
  `SECURITY_AND_SANDBOX.md`, `FOLDER_STRUCTURE.md`, `PROMPT_ARCHITECTURE.md`,
  `DEFAULT_PROMPTS.md`.

## Non-goals

- A generic game designer for arbitrary games (removed in V3).
- Real-time physics rendering or 3D graphics (the animation is a simple 2D simulation).
- More than 2 teams, or more than 1 fighter per team.
- WebSocket push (presence and updates are polled; push may be added later).
