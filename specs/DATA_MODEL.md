# Data Model (V4 — Taekwondo)

## User

```text
User
- id
- username
- email
- password_hash
- role            # admin | teacher | student
- last_seen_at    # presence
- created_at
- updated_at
```

## Team

```text
Team
- id
- match_id         # FK -> matches
- player_id        # the user who owns this team
- name
- difficulty       # easy | medium | hard (the match's difficulty)
- configuration_json   # {"archetype": str|null, "strategy": str, "strategy_preset": str|null}
- created_at
- updated_at
```

A **Team** owns exactly **one** **Player** agent (the fighter). (The point-buy cost of a
team is computed from its fighter's attribute sliders at validation time, not stored.)
`configuration_json.strategy` is the team's free-text strategy notes (shared to the
engine as `instructions`); `configuration_json.strategy_preset` holds the selected
strategy id. On save, the preset's brain fields (persona, goal, skills, tools, params)
and its body attribute allocation for the match difficulty are applied to the fighter.

## Player (agent / fighter)

```text
Player
- id
- team_id          # FK -> teams
- slot             # always 1 (a team has a single fighter)
- configuration_json
- created_at
```

`configuration_json` holds the **brain** and **body** of the fighter (see
`AGENT_ARCHITECTURE.md`):

```text
{
  "name": "My Fighter",

  "brain": {
    "persona": "A patient counter-fighter who reads the opponent.",
    "goal": "Make the opponent miss, then punish with a kick.",
    "task": "defend and counter",
    "skills": [
      {"id": "counter_attack", "title": "Counter-attack",
       "what": "Bait the opponent's attack and punish it.",
       "effect": "Turns aggression into openings for high-damage counters."}
    ],
    "tools": ["retreat", "block", "dodge", "front_kick", "punch"],
    "sensors": ["distance", "own_health", "own_stamina", "own_attributes", "fight_history", "score"],
    "memory": {"type": "short_term", "size": 8},
    "model": "ollama:llama3.2",
    "params": {
      "temperature": 0.7,
      "max_tokens": 256,
      "top_p": 1.0,
      "frequency_penalty": 0.0,
      "presence_penalty": 0.0
    }
  },

  "body": {
    "actuators": ["advance", "retreat", "jump", "front_kick", "roundhouse_kick",
                  "back_kick", "axe_kick", "punch", "block", "dodge"],
    "parameters": {
      "kick_speed": 5,
      "kick_power": 5,
      "precision": 5,
      "defense": 5,
      "agility": 5,
      "stamina": 5,
      "reach": 5
    }
  }
}
```

The `what`/`effect` strings for the 7 body parameters are the auto-explainable metadata
shown in the GUI. They live once in the central body registry
(`body/parameters.py`), not duplicated per fighter. The point-buy cost is computed from
`body.parameters[*]` (each slider point above 1 costs 1) at validation time (not stored).

## Match

```text
Match
- id
- host_id
- guest_id
- status          # created | invited | accepted | ready | running | finished
                  #   | cancelled | declined | failed
- difficulty      # easy | medium | hard
- host_ready
- guest_ready
- final_state_json   # rounds, health, winner
- seed            # reproducible randomness
- created_at
- started_at
- finished_at
```

## Event (interaction log)

```text
Event
- id
- match_id
- sequence_number
- event_type      # MATCH_STARTED, ROUND_STARTED, EXCHANGE_STARTED, DECISION,
                  #   MOVEMENT, ATTACK, HIT, BLOCK, DODGE, DAMAGE, STAMINA,
                  #   ROUND_WON, MATCH_FINISHED
- actor_id
- payload_json    # full trace for DECISION events: prompt, model, model params,
                  #   raw + parsed decision, athlete attributes, combat outcome
- created_at
```

## AppSetting

```text
AppSetting
- id
- key              # "provider_models", "default_model",
                   #   "core_rules", "core_physics", "core_referee",
                   #   "strategy_presets"
- value            # JSON
```

Used for admin-editable settings: the model list per provider, the global default model,
the three **core** files (rules, physics, referee), and the **strategy presets** that the
admin can edit.

---

The exact SQLAlchemy schema is implemented only after the domain objects and workflows
are defined.
