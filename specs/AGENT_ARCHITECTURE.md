# Agent Architecture

This is the canonical description of how an AI taekwondo fighter is built. The whole
platform follows one idea:

> The **brain** decides what to do. The **body** does it. The **core** decides what
> happens next.

Everything the advanced student sees in the **Advanced view** is a file that describes
one of these three parts.

---

## 1. The three parts

```text
BRAIN (the LLM agent)
├── persona     who the fighter is
├── goal        what the fighter wants (win the round / fight)
├── task        what the fighter is doing right now (attack, defend, close distance)
├── skills      the playbook: what the fighter KNOWS
├── tools       the connectors: what the fighter CAN do
├── sensors     what the fighter can SEE
└── memory      a small short-term memory (this round)

        tools ↓                sensors ↑
BODY (the fighter's physical body)
├── actuators   the moves: advance, retreat, jump, kicks, punch, block, dodge
└── parameters  7 skills (sliders 1–10), bought with the budget

             actuators execute moves
                    ↓
CORE / REFEREE (the world)
├── rules       rounds, KO, timeout, win condition
├── combat      range, hit chance, block/dodge, damage, stamina (deterministic, seeded)
└── environment  arena, positions, health, stamina, rounds (the fight state)
```

- **Brain** is the LLM (a model chosen from the providers).
- **Body** is a small, deterministic piece of code.
- **Core** is the deterministic referee + combat. It is **not** an LLM.

---

## 2. Tools vs skills (the key distinction)

These are **two different things**, and teaching the difference is part of the learning.

| | Tool | Skill |
|---|---|---|
| Meaning | What the fighter **can** do | What the fighter **knows** |
| Kind | Code connector brain → body | Natural-language playbook |
| Example | `roundhouse_kick` (calls the body's kick actuator) | "When the opponent advances, counter with a back kick" |
| Stored in | `tools.yaml` | `skills/*.md` |
| Shows | Permission / capability | Strategy / knowledge |

Together they explain a decision: the fighter **could** kick (tool), and **chose** to
counter-kick (skill).

### Tool definition

```yaml
- id: roundhouse_kick
  action: ROUNDHOUSE_KICK
  actuator: roundhouse_kick
  params: [power, height]
  requires: [kick_speed, kick_power]
  what: "A fast circular kick with the instep."
  effect: "Mid damage and mid range; the workhorse kick of taekwondo."
```

A tool:
- links an `action` (what the brain outputs) to an `actuator` (a body move);
- lists the parameters it needs;
- lists the body parameters it uses (`requires`) — this is also the **permission** the
  brain has.

### Skill definition

```markdown
# Skill: Counter-attack

## What it is
Bait the opponent's attack, block or dodge it, then punish with a back kick.

## Effect
Turns the opponent's aggression into openings for high-damage counters.
```

Skills are written by the advanced student and injected into the brain's prompt, so the
LLM "knows" the strategy.

---

## 3. The other brain pieces

- **Persona / system instructions** — who the fighter is (e.g. "a patient counter-fighter").
- **Goal** — the objective (win this round).
- **Task** — the current job (attack / defend / close distance); this is the `action_hint`
  the engine sends.
- **Sensors** — what the brain may read: distance to the opponent, its own health and
  stamina, its own attributes, the round history, and the score. It must **not** read the
  opponent's hidden attributes.
- **Memory** — a small short-term memory: the messages of the current round. There is no
  long-term memory in this version.
- **Prompt** — assembled from the pieces above plus a **side-specific arena guide** (a
  1D distance axis: your position, the opponent's position, and the distance between
  you), so the model knows which direction is "forward" and returns in-range moves.
- **Strategy** — a complete preset chosen in the fighter configuration: the brain
  (persona, goal, skills, tools, model parameters) plus a body attribute allocation per
  match difficulty (easy / medium / hard) that respects each difficulty's budget. Three
  defaults (Aggressive / Defensive / Neutral) are seeded and the admin can add more.

---

## 4. Auto-explainable: `what` + `effect`

Every editable or readable element carries **two** plain-language fields:

```text
what    — what this thing IS (a short definition)
effect  — what it CHANGES on the fighter or the game (cause → effect)
```

This rule applies to:

- the 7 body parameters,
- every tool,
- every skill,
- every actuator,
- every rule and combat knob in the core.

The simple GUI shows `what` under each control and `effect` as a hint. The advanced view
shows both next to every field.

---

## 5. The files (advanced view)

The advanced student edits their **own** agent files; the core files are read-only.

```text
My fighter (editable)
├── agent.md       persona · goal · task
├── skills/*.md    playbooks (one file per skill)
├── tools.yaml     brain → body connectors (+ permissions)
└── body.yaml      actuators + the 7 parameters

Core (read-only for students; admin-editable)
├── rules.yaml     rounds, KO, timeout, win condition
├── physics.yaml   range / hit / damage / stamina constants
└── referee.md     what the deterministic referee does
```

- YAML files are validated and reconciled back into the structured config.
- Markdown files are stored verbatim as authored text.
- The admin can edit the core files; critical parameters show a caution legend, and the
  admin can **restore defaults**.
