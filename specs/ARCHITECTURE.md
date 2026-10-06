# Architecture

## 1. High-level model

```text
Browser
  |
  v
Flask Web Application
  |
  +-- Authentication & Presence
  +-- General Settings (admin)
  +-- User Administration (admin)
  +-- Matchmaking (invite / accept / ready-up)
  +-- Fighter Configuration (simple + Advanced file view)
  +-- Match (live simulation, history, interaction log)
  +-- Graphical Fight Simulation (independent module)
  |
  v
Application Services
  |
  +-- Matchmaking / Presence / Team / Match / Settings services
  |
  v
Domain (taekwondo) — see AGENT_ARCHITECTURE.md
  |
  +-- brain/   the LLM agent (persona, goal, task, skills, tools, sensors, memory)
  +-- body/    the physical body (actuators, 7 parameters)
  +-- core/    the deterministic world (rules, combat, environment)
  +-- engine   orchestrates brain -> body -> core, emits events
  |
  +------------------+
  |                  |
  v                  v
PostgreSQL          Redis
```

## 2. Architectural boundaries

### Web layer

HTTP, authentication, presence, forms, GUI, the Advanced file view, user administration,
and the graphical simulation (client-side). No fight rules or combat here.

### Application layer

Workflows: create/invite/accept/ready fights, configure fighters (validate budget), run
the fight (enqueue to worker), persist the interaction log, expose history, and manage
settings (including the core files and the strategy presets the admin can edit).

### Domain layer (brain / body / core)

- **brain/** — the LLM agent: its persona/goal/task, its skills (playbook), its tools
  (brain→body connectors, also its permission list), its sensors (perception), and its
  short-term memory. Produces a **decision** (`{message, move, action, height, power,
  distance}`).
- **body/** — the physical body: a move library (actuators) and the 7 budget parameters.
  Executes the decision.
- **core/** — the deterministic referee + world: rules, combat (seeded), and environment
  state. Scores by health depletion and KO. **Not an LLM.**
- **engine.py** — the round/exchange loop that wires the three together and emits the
  event stream.

### Infrastructure layer

PostgreSQL, Redis (queue + presence), the LLM provider registry, and the filesystem.

## 3. The interaction loop

```text
for each round (best of 3):
    reset health/stamina/positions
    until a fighter is KO'd or the exchange cap is reached:
        EXCHANGE:
            BODY:  both fighters move (advance/retreat/jump/hold)
            BRAIN: both brains -> decision (uses tools + skills)
            CORE:  resolves range/hit/block/dodge, damage, stamina
        CORE:    checks KO / timeout
    CORE:      scores the round (highest health wins)
```

All randomness lives in the core and is seeded per match, so a run is reproducible.

## 4. Auto-explainable

Every parameter, tool, skill, actuator, rule and combat knob carries `what` (definition)
and `effect` (what it changes on the fighter/game). The GUI shows both; the Advanced view
shows them next to every field.

## 5. The interaction log (event sourcing)

Events: `MATCH_STARTED`, `ROUND_STARTED`, `EXCHANGE_STARTED`, `DECISION` (message, prompt,
model, params, attributes, `skill_id`/`tool_id`), `MOVEMENT`, `ATTACK`, `HIT`, `BLOCK`,
`DODGE`, `DAMAGE`, `STAMINA`, `ROUND_WON`, `MATCH_FINISHED`. Events are persisted
incrementally (one commit per event) so the live view updates in real time.

## 6. Multi-user fights

`created → invited → accepted → (both ready) → running → finished/cancelled/declined`.
1v1; each user owns one Team of one fighter. A fight is enqueued exactly once.

## 7. Graphical simulation (independent)

`app/web/static/js/sim/` plays the event log sequentially: two sprite-based fighters on a
side-view arena, health + stamina bars, a distance gauge, and per-action animation
(idle/run/jump/attack/hit/death). Sprites come from the Street Fighter reference
(`app/web/static/img/fighters/{red,blue}/`). It is self-contained and replaceable.
