# Taekwondo — Game Specification (V4)

This document is the authoritative, detailed specification for the **single game**
implemented by AI Game Lab V4: a taekwondo fight between two AI fighters.

The game is kept **generic-free**: the whole platform is optimized for this one sport.
The layered architecture (web → application → domain → infrastructure), the LLM
multi-provider abstraction, the multi-user matchmaking, and the interaction log are all
retained from V3 — but the beach-volleyball engine is replaced by this taekwondo engine.
The move set and visual assets are adapted from the open-source 2D fighting game
[`alinikan/StreetFighter`](https://github.com/alinikan/StreetFighter) (sprites CC-0).

---

## 1. Roles and team structure

- A **Team** is a single **Fighter** (agent). There is **no partner**.
- Each of the two users in a match owns one Team, and configures its single Fighter.

Each **Fighter (agent)** carries two independent sets of configuration:

1. **Athlete attributes** — 7 numeric skills (section 4) that drive the physical
   simulation (how well the body executes).
2. **LLM configuration** — the model and model parameters (section 5) that drive the
   *decisions* (what the mind chooses to do).

This separation is the pedagogical heart of the app: the **mind** (LLM) decides the
tactics; the **body** (attributes) determines whether the execution succeeds.

---

## 2. Arena and coordinate system

- The arena is a **1D line**: fighter positions are scalars `x ∈ [0, 100]`.
- The **red** fighter (team 0) starts at `x = 20`, facing **+x** (toward the opponent).
- The **blue** fighter (team 1) starts at `x = 80`, facing **−x**.
- **Distance** between the fighters is `|x_red − x_blue|`, range `0..100`.
- A fighter "advances" (moves toward the opponent) or "retreats" (moves away); the core
  clamps every position to `[0, 100]` so nobody leaves the arena.
- **Facing** is derived from relative position: a fighter always faces the opponent.

## 3. Match structure and rules

- **Fighters:** exactly 2 (red / blue), 1 per team, no substitutions.
- **Win condition:** best of **3 rounds** (first to win **2 rounds**).
- **Round state:** each round starts with **health = 100** and **stamina = 100** for both
  fighters, and an **exchange counter = 0**.
- **Round end:**
  - **KO** — a fighter's health reaches `≤ 0`; the opponent wins the round.
  - **Timeout** — the exchange counter reaches the cap (`max_exchanges`); the fighter
    with the **higher remaining health** wins the round. On a tie, the fighter who dealt
    the **more total damage** in the round wins; if still tied, team 0 (red) wins.
- **Exchanges** are the atomic unit of play (section 3.1). Both fighters decide
  simultaneously; the deterministic core resolves the outcome.

### 3.1 The exchange loop

```text
EXCHANGE:
    BODY:  apply each fighter's move (advance/retreat/jump/hold) -> positions, distance
    BRAIN: each fighter -> decision {move, action, height, power, distance}
    CORE:  for each attacker: range check -> hit/block/dodge -> damage
    CORE:  stamina costs + recovery; health clamp; KO/timeout check
```

All randomness lives in the core and is seeded per match (`match.seed`), so a run is
reproducible.

---

## 4. Athlete attributes (physical/technical performance)

Every agent has 7 performance parameters valued from `0.0` (poor) to `1.0` (elite).
Internally they are stored as floats; in the UI they are **sliders 1–10** mapped by the
engine to `0.1 – 1.0` (`value = slider / 10`).

| # | UI label | Engine name | Meaning | Slider ends |
|---|----------|-------------|---------|-------------|
| 1 | Kick Speed | `kick_speed` | How fast strikes land; shortens the opponent's reaction window. | 1 Slow Telegraph → 10 Lightning Kick |
| 2 | Kick Power | `kick_power` | Base damage of every strike. | 1 Feather Tap → 10 Bone Breaker |
| 3 | Precision | `precision` | Accuracy of landing the chosen target zone (head vs body). | 1 Wild Swings → 10 Laser Guided |
| 4 | Defense | `defense` | How well blocks reduce incoming damage. | 1 Open Guard → 10 Iron Wall |
| 5 | Agility | `agility` | Footwork speed and dodge success. | 1 Heavy Footed → 10 Ghost Steps |
| 6 | Stamina | `stamina` | Energy budget and recovery; low stamina degrades everything. | 1 Gassed Out → 10 Endless Tank |
| 7 | Reach | `reach` | Effective striking range advantage. | 1 Short Limbs → 10 Long Reach |

### 4.1 The deterministic combat core

On every exchange the deterministic core (seeded RNG — reproducible) resolves each
attacker's strike:

1. **Range check** — an attack only lands if the current distance is within the attack's
   effective range, scaled by the attacker's `reach`.
2. **Defense** — the defender's chosen action matters: `BLOCK` reduces damage by the
   defender's `defense`; `DODGE` has a chance (driven by `agility`) to avoid the strike
   entirely; otherwise the strike lands at full force.
3. **Hit chance** — a strike must also connect: it is raised by the attacker's
   `kick_speed` and lowered by the defender's `agility` and by targeting the `HEAD`
   (harder to land) instead of the `BODY`.
4. **Damage** — `base_damage(action, height) + power * power_scale`, scaled by the
   attacker's `kick_power`; reduced by a successful block.
5. **Stamina** — every action has a cost; each exchange also recovers a small amount. Low
   remaining stamina penalizes hit chance and damage.

### 4.2 Trade-offs (behavior engine)

- **Power vs stamina:** higher `power` deals more damage but costs more stamina.
- **Head vs body:** `HEAD` strikes deal more damage but are harder to land (require
  `precision`) and slightly slower.
- **Speed vs damage:** fast, cheap kicks (`FRONT_KICK`, `PUNCH`) land often but deal
  little; heavy kicks (`BACK_KICK`, `AXE_KICK`) deal a lot but are slow and exhausting.
- **Offense vs defense:** `BLOCK`/`DODGE` cost stamina and deal no damage, but they blunt
  or avoid the opponent's strike.

---

## 5. LLM model configuration (the "mind")

Each Fighter agent also selects an **LLM model** from the providers defined in the
environment (`LLM_PROVIDERS`), plus standard model parameters:

- `model` (`provider:model`)
- `temperature`
- `max_tokens`
- `top_p`
- `frequency_penalty`, `presence_penalty`
- `stop` (response format is always JSON, enforced by the prompt)

The LLM receives the current fight state **plus the shared round context** (the messages
every agent has produced so far this round) and returns a **message + structured
decision**:

```json
{
  "message": "I close the distance and throw a roundhouse kick to the head",
  "move": "ADVANCE"|"RETREAT"|"JUMP"|"HOLD",
  "action": "FRONT_KICK"|"ROUNDHOUSE_KICK"|"BACK_KICK"|"AXE_KICK"|"PUNCH"|"BLOCK"|"DODGE",
  "height": "HEAD"|"BODY",
  "power": 0.0..1.0,
  "distance": 0.0..1.0
}
```

- `move` — the footwork: advance, retreat, jump, or hold position.
- `action` — the technique (an attack, or a defensive block/dodge).
- `height` — target zone for attacks (ignored for block/dodge).
- `power` — effort; more power = more damage + more stamina cost.
- `distance` — the desired engagement distance (informational; the core uses the actual
  resulting positions).

The prompt sent to the LLM includes an explicit, **side-specific arena guide** (see §2):
the fighter's own position, the opponent's position, and the distance between them, so
models return sensible movement directions and legal actions.

The **interaction log** records, for every decision: the message, the prompt, the model,
the model parameters, the raw response, the parsed decision, the athlete attributes, and
the combat outcome (range, hit/block/dodge, damage, stamina).

### 5.1 Model parameter education

Every model parameter shown in the UI must carry a plain-language description of **how
it changes the agent's behavior**, e.g.:

- **Temperature** — how varied/creative the decisions are (low = predictable).
- **Max tokens** — how long the agent's reasoning/output can be.
- **Top-p** — narrows/expands the vocabulary sampled for a decision.
- **Frequency/presence penalties** — reduce repeated wording/ideas.
- **System prompt** — the persona/strategy the agent is given.

---

## 6. Point-buy economy and difficulty

The user distributes a **budget** across the 7 athlete attributes of their **single
fighter**. Each slider point (1–10) costs **1 point**; every attribute defaults to **1**
(costing 0). Internal float scale: `0.1 – 1.0`.

| Difficulty | Budget | Average attribute level achievable |
|-----------|-------------|------------------------------------|
| EASY | 45 | ~7.4/10 — an elite all-rounder |
| MEDIUM | 25 | ~4.5/10 — a specialized fighter |
| HARD | 12 | ~2.7/10 — mandatory flaws |

Matches are **1v1 human-vs-human**: each of the two users receives the same difficulty
budget. (A single-player "vs AI" mode is reserved for a future version.)

### 6.1 Pre-set archetypes (quick setup, 25 points each — tuned for Medium)

- **THE KICKER (Powerhouse)** — heavy kicks, long reach, slow on the ground.
  Allocates: Kick Power, Reach, Precision, Kick Speed, Stamina.
- **THE GHOST (Speed Demon)** — covers ground, chain kicks, perfect dodges.
  Allocates: Agility, Kick Speed, Precision, Stamina.
- **THE WALL (Counter-fighter)** — blocks everything, punishes mistakes.
  Allocates: Defense, Stamina, Kick Power, Agility.

### 6.2 Strategy presets (complete game plan, applies to the fighter)

The user picks a **strategy** that pre-fills the fighter's *brain* (persona, goal,
skills, tools, and model parameters) **and** a *body* attribute allocation per match
difficulty (easy / medium / hard) that stays within that difficulty's point-buy budget.
Three defaults are seeded, and the admin can create more:

- **Aggressive** — attack-first: press forward and throw power kicks, high risk. Persona
  "fearless attacker", goal "win fast with a heavy kick", skills `pressure_fighting`/
  `head_hunting`, tools `advance, front_kick, roundhouse_kick, back_kick, axe_kick`,
  higher `temperature`; body favors power and speed at every budget.
- **Defensive** — defense-first: block/dodge everything, counter the error. Persona
  "patient counter-fighter", goal "make the opponent miss, then punish", skills
  `counter_attack`/`distance_control`, tools `retreat, block, dodge, front_kick, punch`,
  lower `temperature`; body favors defense and stamina at every budget.
- **Neutral** — balanced, all skills and all tools, default `temperature`; body balanced
  at every budget.

Strategies are stored in the `strategy_presets` AppSetting and managed by the admin.

---

## 7. Match flow (multiuser)

```
player A: create fight (choose difficulty)                    status=created
          -> invite online player B                           status=invited
player B: accept                                              status=accepted
both:     configure fighter (sliders/archetype + model + params)
both:     ready                                               -> auto-start
          -> FightEngine simulates rounds/exchanges           status=running
          -> finished                                         status=finished
```

The teacher (and any user) can browse **match history** (all finished fights stored in
the database with their full interaction log).

---

## 8. Graphical simulation (independent module)

The match view renders a **simple but accurate** animation of the two fighters on a
side-view arena. This is an **independent entity** — a self-contained module
(`app/web/static/js/sim/`) driven only by the event stream, so it can be customized and
enhanced later without affecting the rest of the app.

Requirements:

- A side-view arena (background image + ground line) with two sprite-based fighters
  (red / blue, from the Street Fighter reference).
- Health bars and stamina bars above each fighter, plus a round scoreboard.
- A distance gauge (or the two positions) showing how far apart the fighters are.
- Fighters animate per action (idle / run / jump / attack1 / attack2 / attack3 / hit /
  death) using the per-action sprite strips; each fighter flips to face its opponent.
- The animation polls the event stream live (events are persisted incrementally by the
  worker) and is replayable from the stored event log (play / pause / seek / speed).
- A visible "running…" indicator while the worker is executing.
- The simulation **auto-plays on load**.

---

## 9. Agent architecture & blueprint files

A fighter is an **embodied agent** (brain / body / core). The full model — persona, goal,
task, skills, tools, sensors, actuators, memory, and the `what`+`effect` explainability
rule — is defined in **`AGENT_ARCHITECTURE.md`**.

In the **Advanced view**, the advanced student edits these files for their own fighter:

```text
agent.md      persona · goal · task
skills/*.md   playbooks
tools.yaml    brain → body connectors (and permissions)
body.yaml     actuators + the 7 parameters
```

and can read (but not modify) the core files:

```text
core/rules.yaml
core/physics.yaml
core/referee.md
```

The admin can edit the core files (with a caution legend on critical parameters and a
"restore defaults" action).
