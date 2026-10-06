# AI Game Lab — User Guide (Taekwondo Fighter)

This guide explains how to use AI Game Lab V4: creating fights, configuring your
fighter, running the fight simulation, and reading the interaction log.

---

## 1. Overview

AI Game Lab is an educational, multi-user platform for learning how large language
models work, through a single game: a **taekwondo fight**. A fight is played by two
fighters (one per user). Each fighter is the combination of:

- a **mind** — an LLM (model + model parameters) that decides the tactics;
- a **body** — 7 athlete attributes (sliders 1–10) that determine whether the execution
  works.

You configure both, run the fight, and read the interaction log to see how each decision
and each attribute shaped the result.

Main areas:

1. **Matchmaking** — create a fight, invite an online player, accept, ready up.
2. **Fighter configuration** — set your fighter's attributes, archetype, model, and
   model parameters.
3. **Match** — the live graphical simulation and the interaction log.
4. **History** — browse every fight.

### Roles

| Role | Typical use |
| --- | --- |
| `admin` | Manages users and settings. |
| `teacher` | Browses fight history; manages the class. |
| `student` | Configures fighters and plays fights. |

---

## 2. Logging in

Enter your username and password. New students can register from the login page; teachers
and administrators are usually created by an administrator.

---

## 3. Matchmaking

Open **Matchmaking**.

### 3.1 Create a fight

Choose a **difficulty** (Easy / Medium / Hard — this sets the point budget for building
your fighter) and click **Create**.

### 3.2 Invite a player

On the fight page, pick an **online player** and click **Invite**. They can **Accept** or
**Decline**.

### 3.3 Ready up

After accepting, each player configures their fighter (section 4) and clicks **I'm ready**.
When both are ready, the fight starts automatically.

---

## 4. Configuring your fighter

Click **Configure my fighter** on the fight page.

### 4.1 Athlete attributes (1–10 sliders)

Your fighter has 7 skills; drag the sliders. Every skill shows a plain-language
description of how it changes behavior:

- **Kick Speed** — how fast your strikes land; raises your hit chance.
- **Kick Power** — how hard you hit; raises damage.
- **Precision** — accuracy of the chosen target zone (head vs body).
- **Defense** — how well your blocks reduce incoming damage.
- **Agility** — footwork speed and dodge success.
- **Stamina** — energy reserve and recovery; low stamina degrades everything.
- **Reach** — effective striking range advantage.

### 4.2 Point budget

Each slider point above 1 costs 1 point, from the difficulty budget (Easy 45, Medium 25,
Hard 12). All attributes default to 1 (free). If you exceed the budget, the app rejects
the save and tells you the cost.

### 4.3 Preset archetypes

For a quick start, pick an archetype (applied to your fighter):

- **The Kicker (Powerhouse)** — heavy kicks and long reach, slow on the ground.
- **The Ghost (Speed Demon)** — covers ground and chains fast kicks.
- **The Wall (Counter-fighter)** — blocks everything and punishes mistakes.

### 4.4 LLM model & parameters

Your fighter selects an **LLM model** (from the providers configured in the environment)
and model parameters, each with a short explanation:

- **Temperature** — how varied/creative the decisions are.
- **Max tokens** — max length of the response.
- **Top-p** — narrows/expands the sampled vocabulary.
- **Frequency / presence penalty** — reduce repetition.
- **System prompt** — the strategy/persona given to the agent.

### 4.5 Advanced view (view agent files)

On the fighter page, the **View agent files** tab shows your fighter as the files that
make up an agent: `agent.md` (persona/goal/task), `skills/*.md` (the playbook),
`tools.yaml` (brain→body connectors), and `body.yaml` (actuators + the 7 parameters).
These are read-only here — you edit them through the structured form. The **Core files**
section shows the game's rules, combat, and referee (read-only for students).

### 4.6 Strategy preset (Aggressive / Defensive / Neutral)

The **Strategy preset** selector pre-fills your fighter with a ready-made game plan: the
*brain* (persona, goal, skills, tools, model parameters) **and** the *body* attribute
allocation for the match's difficulty (easy / medium / hard), each within that
difficulty's budget:

- **Aggressive** — press forward and throw heavy kicks, high risk, high reward.
- **Defensive** — block/dodge everything, counter the opponent's mistakes.
- **Neutral** — balanced, all-round play.

Administrators can add more alternatives in **Settings → Strategy presets**.

---

## 5. The fight

Open **Matchmaking → your fight**, or **History → View**.

### 5.1 The graphical simulation

A side-view arena shows the two fighters (red and blue). Each exchange animates the
fighters' footwork (advance / retreat / jump), their kicks and punches, and their
reactions (take a hit, block, dodge). Health and stamina bars sit above each fighter, a
distance gauge shows how far apart they are, and a round scoreboard tracks the best-of-3
score. A **"▶ Fight running…"** indicator confirms the fight is in progress. The
animation is a separate, replaceable module and **auto-plays on load**.

### 5.2 The interaction log

The sidebar records every event, so you can trace *why* an exchange was won or lost:

- **Decision** — each fighter's natural-language **message** and its parsed decision
  (move, action, height, power), plus the model and model parameters used.
- **Movement** — each fighter's footwork (advance / retreat / jump / hold).
- **Attack** — the technique thrown and its result (hit / miss / dodged).
- **Block / Dodge / Hit / Damage** — how the defender resolved the strike and the damage
  dealt.
- **Stamina** — the stamina cost and remaining reserves after each exchange.
- **Round won / Match finished** — the round and fight outcome.

### 5.3 Controls

- **Stop** — cancel a running/queued fight.
- **Cancel** — abandon a fight that hasn't started.
- **Delete** — remove a fight and its history.

---

## 6. History

Open **History** to browse every fight (finished and otherwise). Open a fight's **Log** to
see its full interaction log and final state. This is where teachers review class results.

---

## 7. Settings & users (admin)

- **Settings** — edit the model list per provider and the global default model.
- **Settings → Core files** — edit the rules and combat knobs (with a caution legend on
  critical parameters) and the referee description; restore defaults at any time.
- **Users** — create accounts, change roles, delete users.

---

## 8. Key concepts

| Concept | Meaning |
| --- | --- |
| **Team** | One fighter, owned by one user. |
| **Fighter (agent)** | An LLM (mind) + 7 athlete attributes (body). |
| **Attribute** | A physical/technical skill (0.1–1.0) that drives the combat. |
| **Model** | An LLM, referenced `provider:model`. |
| **Decision** | A structured action `{move, action, height, power, distance}` produced by the LLM. |
| **Arena** | A 1D line `x` 0..100; distance is `|x_red − x_blue|`. |
| **Interaction log** | The full trace of every decision and outcome. |

---

## 9. Typical classroom flow

1. The **teacher** creates student accounts (**Users**).
2. Two **students** create/accept a fight and configure their fighters (section 4).
3. They ready up; the fight runs; they watch the simulation and read the log (section 5).
4. The class compares results in **History**, discussing how attributes and model
   parameters changed the outcome.
