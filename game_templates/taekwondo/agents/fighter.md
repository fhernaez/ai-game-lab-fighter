# Agent: Fighter

A taekwondo fighter is an embodied AI agent:

- **Brain (LLM)** — decides what to do: persona, goal, task, skills (playbook), tools
  (permission list), sensors (perception), memory.
- **Body (deterministic)** — 7 attributes (kick speed, kick power, precision, defense,
  agility, stamina, reach) and a move library (actuators).
- **Core (deterministic)** — the rules and combat that turn decisions into outcomes.

Decision protocol:

```json
{"message": "...", "move": "ADVANCE|RETREAT|JUMP|HOLD",
 "action": "FRONT_KICK|ROUNDHOUSE_KICK|BACK_KICK|AXE_KICK|PUNCH|BLOCK|DODGE",
 "height": "HEAD|BODY", "power": 0.0..1.0, "distance": 0.0..1.0}
```
