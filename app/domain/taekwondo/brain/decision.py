"""The brain's decision protocol: a message + a structured move/action.

This module has two jobs:

1. ``parse_decision`` — validate and clamp whatever JSON the LLM returns so a
   malformed or out-of-range decision can never crash the engine.
2. ``build_decision_prompt`` — assemble the prompt the LLM receives. It is built from
   labelled sections (persona, goal, task, skills, tools, sensors, memory) plus an
   explicit **side-specific arena guide** (a 1D distance axis), because models
   otherwise move in the wrong direction or return illegal actions.
"""

from . import skills, tools
from .sensors import render_sensors

# The legal values for each decision field. Footwork (`move`) is always allowed;
# `action` is the permission-gated technique.
MOVES = ["ADVANCE", "RETREAT", "JUMP", "HOLD"]
ACTIONS = ["FRONT_KICK", "ROUNDHOUSE_KICK", "BACK_KICK", "AXE_KICK", "PUNCH", "BLOCK", "DODGE"]
HEIGHTS = ["HEAD", "BODY"]

DEFAULT_DECISION = {
    "message": "",
    "move": "HOLD",
    "action": "FRONT_KICK",
    "height": "BODY",
    "power": 0.5,
    "distance": 0.5,
}


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def parse_decision(parsed, fallback=None):
    """Validate and clamp a parsed LLM output; never raises.

    Returns a fully-formed decision dict, substituting ``fallback`` (or the
    DEFAULT_DECISION) for any missing or invalid field.
    """
    fallback = fallback or dict(DEFAULT_DECISION)
    if not isinstance(parsed, dict):
        return dict(fallback)

    message = str(parsed.get("message", fallback.get("message", "")))

    move = parsed.get("move")
    if move not in MOVES:
        move = fallback["move"]

    action = parsed.get("action")
    if action not in ACTIONS:
        action = fallback["action"]

    height = parsed.get("height")
    if height not in HEIGHTS:
        height = fallback["height"]

    try:
        power = float(parsed.get("power", fallback["power"]))
    except (TypeError, ValueError):
        power = fallback["power"]
    power = _clamp(power, 0.0, 1.0)

    try:
        distance = float(parsed.get("distance", fallback["distance"]))
    except (TypeError, ValueError):
        distance = fallback["distance"]
    distance = _clamp(distance, 0.0, 1.0)

    return {
        "message": message,
        "move": move,
        "action": action,
        "height": height,
        "power": power,
        "distance": distance,
    }


def _arena_guide(team_index, state):
    """Return the side-specific arena guide for the fighter.

    ``team_index`` 0 = red (facing +x), 1 = blue (facing -x).
    """
    own = state.positions[team_index]
    opp = state.positions[1 - team_index]
    if team_index == 0:
        facing = "+x (to the right)"
    else:
        facing = "-x (to the left)"
    return (
        "ARENA COORDINATES (1D line):\n"
        "- The arena runs from x = 0 to x = 100.\n"
        f"- YOU are at x = {own:.1f}, facing {facing}.\n"
        f"- The OPPONENT is at x = {opp:.1f}.\n"
        f"- distance = |your x - opponent's x| = {abs(own - opp):.1f}.\n"
        "- ADVANCE moves you toward the opponent; RETREAT moves you away; "
        "JUMP avoids low attacks; HOLD stays put.\n"
        "- An attack only lands when distance is within your reach."
    )


def _render_state(state):
    return (
        f"round {state.current_round}, health RED {state.health[0]:.0f} vs "
        f"BLUE {state.health[1]:.0f}, stamina RED {state.stamina[0]:.0f} vs "
        f"BLUE {state.stamina[1]:.0f}, rounds {state.rounds_won[0]}-{state.rounds_won[1]}, "
        f"distance {state.distance():.1f}"
    )


def build_decision_prompt(brain, team_name, fighter_name, state, action_hint, round_history, team_index=None):
    """Assemble the brain's prompt as (system, user) messages.

    The user message is built from short, labelled sections so the model always knows
    who it is, what it can do/know/see, where it is on the arena, and the exact JSON it
    must return.
    """
    tool_list = ", ".join(brain.get("tools") or list(tools.TOOL_KEYS))
    skill_text = skills.render_skills(brain.get("skills") or skills.load_default_skills())
    sensor_text = render_sensors(brain.get("sensors"))

    guide = _arena_guide(team_index if team_index is not None else 0, state)

    system = (
        "You are an AI taekwondo fighter. Return a JSON object with a short "
        "natural-language message explaining what you will do, plus your footwork and "
        "technique."
    )
    user = "\n\n".join(
        [
            f"TEAM: {team_name}",
            f"YOU ARE: {fighter_name}",
            guide,
            f"PERSONA\n{brain.get('persona', '')}",
            f"GOAL\n{brain.get('goal', '')}",
            f"TASK\n{action_hint}",
            f"SKILLS (what you know)\n{skill_text}",
            f"TOOLS (what you can do)\n{tool_list}",
            f"SENSORS (what you can see)\n{sensor_text}",
            "CURRENT MATCH STATE:\n" + _render_state(state),
            "WHAT HAS HAPPENED THIS ROUND:\n" + ("\n".join(round_history[-10:]) or "(start of round)"),
            'Return JSON: {"message": "...", "move": "ADVANCE"|"RETREAT"|"JUMP"|"HOLD", '
            '"action": "FRONT_KICK"|"ROUNDHOUSE_KICK"|"BACK_KICK"|"AXE_KICK"|"PUNCH"|"BLOCK"|"DODGE", '
            '"height": "HEAD"|"BODY", "power": 0.0..1.0, "distance": 0.0..1.0}',
        ]
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
