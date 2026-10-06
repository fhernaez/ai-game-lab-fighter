# AI Game Lab — Taekwondo Fighter

**Learn how AI thinks, one exchange at a time.**

A friendly, open-source, browser-based platform where students build their own AI
taekwondo fighter, watch it fight, and — most importantly — understand *why* it fights
the way it does. Through a single, deeply-simulated game, students discover how large
language models actually work: the **brain** (the LLM), the **body** (the athlete's
attributes), and the **core** (the rules and combat).

---

## Why this project (our goals)

- **Teach AI by doing, not just reading.** Students configure the *mind* and the
  *body* of their fighter and see the consequences instantly in the arena.
- **Make AI transparent.** Every decision is logged with its prompt, model,
  parameters, and outcome, so there are no black boxes.
- **Build intuition for the new AI era.** Students learn concepts like prompts,
  tools, skills, sensors, model parameters, and deterministic cores — the same ideas
  behind real agentic systems.
- **Keep it accessible.** It runs in a browser, works offline with a mock model, and
  needs nothing more than Python to start.

> This project is a contribution to the community to help young people understand
> and get involved with AI — theory and practice — and to develop the strengths
> they will need for the new AI era.

---

## What is it?

A multi-user **Flask** application that simulates taekwondo fights between two AI
fighters. Each fighter is an LLM that decides *what* to do, paired with a small
deterministic body that decides *whether it works*. A deterministic referee applies the
rules and combat, so every exchange can be explained and reproduced.

The move set and visual assets are adapted from the open-source 2D fighting game
[`alinikan/StreetFighter`](https://github.com/alinikan/StreetFighter) (sprites CC-0);
see [Attribution](#attribution).

See the `specs/` folder (especially `specs/FIGHTER_SPEC.md`) for the full
specification.

---

## Features

- **A real taekwondo engine** — best of 3 rounds, KO and timeout win conditions, a
  1D arena with distance management, and a seeded deterministic core so fights are
  reproducible.
- **Brain / body / core architecture** — an LLM mind, 7 athlete attributes, and a
  deterministic referee; the clean separation is the whole point of the lesson.
- **Message-driven exchanges** — every fighter explains its decision in natural
  language, and those messages are shared to the rest of the round as context.
- **Point-buy economy** — 7 skills (Kick Speed, Kick Power, Precision, Defense,
  Agility, Stamina, Reach) with Easy/Medium/Hard budgets, preset **archetypes**, and
  preset **strategies** (Aggressive / Defensive / Neutral) that administrators can
  extend.
- **Multi-provider LLMs** — Ollama, any OpenAI-compatible endpoint, or an offline
  mock model; every fighter picks its own model and parameters.
- **A living graphical simulation** — a side-view arena with two sprite-animated
  fighters (idle / run / jump / attack / hit / death), health and stamina bars, a
  distance gauge, autoplay, and play/pause/scrub/speed controls.
- **Full interaction log** — prompt, model, parameters, raw + parsed decision,
  attributes, and the combat outcome of every exchange.
- **Match history**, **multi-user matchmaking**, and **admin tools** for users,
  core files (rules / physics / referee), and strategy presets.

---

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # optional: edit for PostgreSQL / Ollama

flask --app run.py db upgrade   # create / migrate the database schema
flask --app run.py seed         # create the admin user
flask --app run.py run
```

Then open http://localhost:5000 and log in as `admin` / `admin123`
(override with `ADMIN_USERNAME` / `ADMIN_PASSWORD`).

### Docker

```bash
cp .env.example .env
docker compose up -d --build
```

More details:

- `docs/STARTUP_GUIDE.md` — installation, database, Ollama, environment, Docker.
- `docs/USER_GUIDE.md` — matchmaking, fighter configuration, the fight view, history.
- `docs/DEVELOPER_GUIDE.md` — architecture and how to customize and extend.

---

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///instance/app.db` | SQLAlchemy URI |
| `POSTGRES_USER/PASSWORD/HOST/PORT/DB` | *empty* | Build `DATABASE_URL` when unset |
| `REDIS_URL` | *empty* | Redis URL (empty = synchronous runs) |
| `LLM_PROVIDERS` | *empty* | JSON list of providers `{id, type, base_url, api_key, models[]}` |
| `DEFAULT_PROVIDER` / `DEFAULT_MODEL` | `mock` / `mock-model` | Global fallback provider/model |
| `SEED_ON_START` | `false` | Docker entrypoint seeds on boot |

## CLI commands

| Command | Purpose |
| --- | --- |
| `flask db upgrade` | Create / migrate the database schema |
| `flask seed` | Create the admin user |
| `flask create-user USER EMAIL ROLE` | Create a user |
| `flask worker` | Start a background worker for queued fights |

## Tests

```bash
pip install pytest
pytest
```

---

## Attribution

The fighter sprites (warrior and wizard), the background image, the victory icon, the
audio, and the font are adapted from the open-source game
[`alinikan/StreetFighter`](https://github.com/alinikan/StreetFighter). The fighter
sprites are licensed **Creative Commons Zero (CC-0)** — free for commercial and
non-commercial use. The original license text is preserved in
`app/web/static/img/fighters/LICENSE.txt`.

---

## Want to help? Collaborators are very welcome!

This is a living educational project, and there is plenty of room to contribute:

- **Educators** — classroom guides, lesson plans, or new games and exercises.
- **Developers** — frontend polish, better simulation, more LLM providers, tests.
- **AI enthusiasts** — prompt engineering, agent strategies, evaluation ideas.
- **Designers** — fighter sprites, arena visuals, UX improvements.

Found a bug or have an idea? Open an issue or send a pull request. We review
contributions with care and credit every collaborator.

---

## About us — DOMAH SA

This project is created and maintained by **DOMAH SA**.

At Domah we specialize in comprehensive **customized software development focused on
AI applied to process optimization**. We also integrate **IoT, domotics, and automation
solutions**, enhancing productivity while minimizing environmental impact through
expert management and engineering.

We build this game as our way of giving back: a tool for young people to understand
and get involved with AI, both in theory and in practice.

Website: [domah.com.ar](https://domah.com.ar)

### Contact

- Email: [ingenieria@domah.com.ar](mailto:ingenieria@domah.com.ar)
- Phone / WhatsApp: +54 9 11 5958 5257

---

## License

Released under the **MIT License** — see [LICENSE](LICENSE). You are free to use,
modify, and share this project with attribution. Contributions are governed by
[CONTRIBUTING.md](CONTRIBUTING.md).

---

## Project structure

```
app/
├── web/            # routes, templates, static (simulation + fighter sprites)
├── application/    # matchmaking, presence, team, match, settings services
├── domain/taekwondo/   # brain/, body/, core/ (rules, combat, world) + engine
├── infrastructure/ # LLM provider registry, queue (Redis/rq)
└── models.py       # Match, Team, Player, Event, User, AppSetting
```

Happy fighting — and welcome to the new AI era.
