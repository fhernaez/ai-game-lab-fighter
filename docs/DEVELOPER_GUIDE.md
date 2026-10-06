# AI Game Lab — Developer Guide (Taekwondo Fighter)

This guide explains the V4 architecture and how to customize and extend the taekwondo
fighting application.

---

## 1. Architecture

```text
Browser (Jinja2 + HTMX + vanilla JS)
   |
   v
web/            routes + templates + static (sim/)
   |
   v
application/    matchmaking, presence, team, match, settings services
   |
   v
domain/taekwondo/   brain/ body/ core/ engine  (no Flask)
   |
   v
infrastructure/ LLM provider registry, database (SQLAlchemy), Redis/rq queue
```

Key rules:

- **Domain is Flask-free** (`app/domain/taekwondo/*`).
- **No game logic in routes**; routes call services, services call the domain.
- **The graphical simulation is independent** — `app/web/static/js/sim/`
  consumes only the event stream; replace it without touching anything else.
- **Seeded randomness** — the fight engine uses a seeded `random.Random`, so fights are
  reproducible.

## 2. Repository layout

```
app/
├── web/            # auth, users, settings, matchmaking, teams, matches, history, api
│   ├── templates/  # base, auth, users, settings, matchmaking, teams, matches, history
│   └── static/js/sim/   # independent simulation module
├── application/    # matchmaking_service, presence_service, team_service, match_service,
│                   #   settings_service, seed
├── domain/taekwondo/
│   ├── brain/      # agent.py, skills.py, tools.py, sensors.py, memory.py,
│   │               #   decision.py, strategies.py, render.py (agent file view)
│   ├── body/       # body.py, actuators.py, parameters.py (7 skills, budget, archetypes)
│   ├── core/       # rules.py, physics.py, world.py, defaults.py (admin-editable knobs),
│   │               #   render.py (core file view)
│   ├── engine.py   # FightEngine
│   └── events.py   # event types
├── infrastructure/ # llm/ (registry, mock, openai_compatible), queue.py
└── models.py       # Match, Team, Player, Event, User, AppSetting
```

## 3. The fight engine

`app/domain/taekwondo/engine.py` runs an exchange-based, message-driven fight. Each round
is a series of **exchanges**: both fighters decide simultaneously (each LLM returns a
`{move, action, height, power, distance}` decision), then the deterministic core resolves
the exchange.

- `core/physics.py` — footwork (`move_step`), attack range (`attack_range`), hit chance
  (`hit_chance`), dodge/block, damage, and stamina. The per-technique shape (range, base
  damage, stamina, speed) is in `TECHNIQUES`; the tunable scalars are in `defaults.KNOBS`.
- `brain/decision.py` — the message + decision protocol and the prompt, which includes a
  **side-specific** arena guide (own position, opponent position, distance) so models
  move in the right direction.
- `events.py` — `DECISION`, `MOVEMENT`, `ATTACK`, `HIT`, `BLOCK`, `DODGE`, `DAMAGE`,
  `STAMINA`, `ROUND_STARTED`, `ROUND_WON`, `MATCH_FINISHED`.
- Every agent's message is accumulated and shared to later exchanges in the round.
- "Advance" always moves *toward* the opponent and "retreat" always moves *away*,
  regardless of which fighter is on the left, so the fighters can never drift apart.

Events are **persisted incrementally** — `match_service._run` commits each event as the
engine emits it (via an `on_event` callback), so the live view updates in real time. A
failed event write marks the match `failed` (never silently empty). `start_match` is
idempotent: it refuses to enqueue a match that is already `queued` or `running`.

`match_service.build_teams()` materializes the DB teams into the dicts the engine expects
(one fighter per team); `match_service._make_resolver()` builds the
`resolve(model_ref) -> (provider, model)` callable from the LLM registry.

## 4. Extending

### 4.1 Tune the combat / rules (admin)

The tunable rules and combat constants live in `app/domain/taekwondo/core/defaults.py`
(`KNOBS`), each with a `what`/`effect` description and `min`/`max`/`step`. Administrators
edit them in **Settings → Core files**; the values are stored as `AppSetting` rows and a
match snapshots the resolved values (`Match.core_config_json`) at start, so history never
changes when the knobs change. Students read the same files read-only.

### 4.2 Add a technique (kick / punch)

Add an entry to `TECHNIQUES` in `core/physics.py`, add a matching tool in
`brain/tools.py` (action → actuator + `requires`), an actuator in `body/actuators.py`,
and include the action in `brain/decision.py:ACTIONS`. The `ACTION_POSE` map in
`static/js/sim/replay.js` selects the sprite pose.

### 4.3 Add a provider

Add an entry to `LLM_PROVIDERS` (OpenAI-compatible, including Ollama — no code). For a new
provider *type*, subclass `LLMProvider` in `app/infrastructure/llm/` and register it in
`registry.py:build_registry`.

### 4.4 Add a model / migration

Add to `app/models.py`, then `flask db migrate` + `flask db upgrade`.

### 4.5 Add a page

Create a blueprint in `app/web/`, register it in `app/__init__.py:register_blueprints`,
add templates, and a nav link in `base.html`.

### 4.6 Customize the arena animation

The simulation is a set of ES modules in `app/web/static/js/sim/` (`arena.js`,
`fighters.js`, `renderer.js`, `replay.js`, `live.js`, `main.js`), loaded from
`matches/view.html` as `<script type="module">`. It consumes only
`/api/matches/<id>/state` and `/events`. No other code depends on it — replace or
upgrade it freely.

Fighters are drawn as **sprite animations** (`fighters.js` + `renderer.js`): each pose is
a horizontal strip PNG loaded from `app/web/static/img/fighters/{red,blue}/`. `arena.js`
defines the per-fighter frame size and pose→filename map (the blue fighter has no
`Attack3` sprite, so its `attack3` pose reuses `Attack2`). Missing sprites fall back to a
procedural silhouette.

### 4.7 The Advanced view

A fighter's config is stored as structured JSON (`brain` + `body`). The Advanced view
(`teams/advanced.html`) serializes it read-only into the file view (`agent.md`,
`skills/*.md`, `tools.yaml`, `body.yaml`) via `brain/render.py` and `core/render.py`.
Editing happens through the structured form in `teams/configure.html`.

### 4.8 Strategy presets

`brain/strategies.py` defines three presets (Aggressive / Defensive / Neutral), each a
complete game plan: a `brain` (persona, goal, skills, tools, model parameters) plus an
`attributes` map with a body allocation per difficulty (easy / medium / hard) that stays
within that difficulty's budget. The admin manages them in **Settings → Strategy
presets** (`strategy_presets` `AppSetting`); the fighter configuration applies a chosen
strategy to the fighter at save time. `strategy_attributes(strategy, difficulty)`
returns that allocation; `apply_strategy` merges the brain fields.

## 5. Conventions

- Domain Flask-free; services between routes and domain.
- Secrets in env only; never in the DB or rendered files.
- No arbitrary code execution; every LLM decision is validated/clamped.
- Version the rules; match history must never change when the rules change.

## 6. Testing

```bash
pytest
```

Add tests for rules, attributes/budget, combat determinism, fighter config, matchmaking
lifecycle, and history.
