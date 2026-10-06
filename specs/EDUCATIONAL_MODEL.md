# Educational Model

## Goal

Teach how LLMs work by building a taekwondo fighter that is an AI agent. A fighter is a
**brain** (LLM) + **body** (moves and parameters) inside a **world** (rules + combat).

The interface must always answer two questions for every element:

1. **What is this?** (a short definition)
2. **What effect does it have?** (what it changes on the fighter or the game)

These two (`what` and `effect`) are shown together everywhere.

## The core mental model: brain vs body vs world

- **Brain** — decides *what* to do, using its **tools** (what it can do) and its
  **skills** (what it knows).
- **Body** — executes it with **actuators** (moves) and **parameters** (quality).
- **World / core** — applies the rules and combat, and scores.

## Concept progression

1. **The agent** — a team has one fighter; it is an LLM with a persona, goal, and task.
2. **Tools** — what the fighter *can* do (advance, retreat, kicks, punch, block, dodge).
   Tools are the connectors from the brain to the body.
3. **Skills** — what the fighter *knows* (the playbook: when and how to use its tools).
4. **Body parameters** — the 7 qualities (kick speed, kick power, precision, defense,
   agility, stamina, reach), each with a `what` and an `effect`.
5. **The world** — rules and combat (deterministic, seeded) that turn decisions into
   outcomes.
6. **Point-buy economy** — budgets and trade-offs; specialization vs balance.
7. **The interaction log** — reading the full trace (message, tool, skill, parameters,
   outcome) to understand *why* an exchange was won or lost.
8. **Advanced view** — edit the fighter's files (persona, skills, tools, body) and read
   the core files.

**Strategies** are complete presets (Aggressive / Defensive / Neutral, admin-extensible)
that pre-fill a fighter's persona, goal, skills, tools, and model parameters, plus a body
attribute allocation per difficulty that fits that difficulty's budget — the tactical
counterpart to the body archetypes. The **sprite-based fighter figures** in the
simulation make each move (advance, jump, kick, take a hit) visually recognizable,
helping students connect a decision to the physical action.

## Transparency — the interaction log

For every exchange the student can inspect: which fighter acted, the message, the tool
used, the skill (if any), the parameters, the raw + parsed decision, and the combat
outcome. The graphical simulation shows the fighters; the log shows the reasoning.

Do not expose hidden chain-of-thought. Show concise decisions and observable events.
