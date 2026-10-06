# Prompt Architecture

The brain's prompt is assembled from controlled sections. It tells the LLM *who* it is,
*what it can do* (tools), *what it knows* (skills), and *what it can see* (sensors).

## Prompt layers

```text
1.  Persona / system instructions     who the fighter is
2.  Goal                              win this round / fight
3.  Task                              the current job (attack / defend / close distance)
4.  Arena coordinates                 1D axis, positions, distance, facing
5.  Skills                            the playbook (what the fighter knows)
6.  Tools                             what the fighter can do (and its permissions)
7.  Sensors                           what the fighter can see (state, round history)
8.  Memory                            the current round messages (short-term)
9.  Output contract                   return a message + structured decision
```

## Example conceptual prompt

```text
You are the RED fighter on a taekwondo mat.

PERSONA
A patient counter-fighter who reads the game.

GOAL
Make the opponent miss, then punish with a kick.

TASK
Defend and counter-attack.

ARENA COORDINATES (1D line)
- The arena runs from x = 0 to x = 100.
- YOU (RED) are at x = 20, facing +x (to the right).
- The OPPONENT (BLUE) is at x = 80.
- distance = |your x - opponent's x| = 60.
- ADVANCE moves you toward the opponent; RETREAT moves you away.
- An attack only lands when distance is within your reach.

SKILLS (what you know)
- Counter-attack: bait the opponent's attack and punish it.

TOOLS (what you can do)
- retreat, block, dodge, front_kick, punch

SENSORS (what you can see)
- distance, your health, your stamina, your attributes, round history, score

CURRENT STATE
Round 1, health RED 72 vs BLUE 60, stamina RED 55 vs BLUE 40, distance 24.

WHAT HAS HAPPENED THIS ROUND
[RED] I retreat and keep the distance.
[BLUE] I advance and throw a front kick.

Return JSON: {"message": "...", "move": "ADVANCE"|"RETREAT"|"JUMP"|"HOLD",
              "action": "FRONT_KICK"|"ROUNDHOUSE_KICK"|"BACK_KICK"|"AXE_KICK"|"PUNCH"|"BLOCK"|"DODGE",
              "height": "HEAD"|"BODY", "power": 0.0..1.0, "distance": 0.0..1.0}
```

## Important

- The **tools** are the permission list: an action not in the tools list is rejected.
- The **skills** are natural-language strategy; they guide reasoning but never grant new
  capabilities.
- Student-authored text (persona, skills) is clearly marked as fighter configuration and
  must not replace platform or rules text.
- Do not expose hidden chain-of-thought; the decision is a message + structured action.
- The coordinate guide is **side-specific**: the prompt tells each fighter its own
  position, the opponent's position, and the distance, so the model moves in the right
  direction and returns in-range actions.
- A chosen **strategy** pre-fills persona/goal/skills/tools/params before these sections
  are rendered.

## Output protocol

```json
{"message": "I close the distance and throw a roundhouse kick to the head",
 "move": "ADVANCE", "action": "ROUNDHOUSE_KICK", "height": "HEAD", "power": 0.8,
 "distance": 0.2}
```

If the model returns invalid output, the engine falls back to a deterministic default and
records the failure in the interaction log.
