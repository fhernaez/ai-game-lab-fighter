"""The brain's connectors: the tool registry (also the permission list).

A **tool** links an `action` (what the brain outputs) to an `actuator` (a body move),
lists the parameters it needs, and lists the body parameters it uses (`requires`) —
which is also the permission the brain has. An action whose tool is not in the agent's
`tools` list is rejected by the engine.

Footwork (`ADVANCE` / `RETREAT` / `JUMP` / `HOLD`) is a free body capability, not a
tool; only the *technique* actions are permission-gated.
"""

TOOLS = {
    "front_kick": {
        "action": "FRONT_KICK",
        "actuator": "front_kick",
        "params": ["power", "height"],
        "requires": ["kick_speed", "kick_power"],
        "what": "A straight snap kick with the ball of the foot.",
        "effect": "Fast and cheap; low damage. A good tool to keep the opponent honest.",
    },
    "roundhouse_kick": {
        "action": "ROUNDHOUSE_KICK",
        "actuator": "roundhouse_kick",
        "params": ["power", "height"],
        "requires": ["kick_speed", "kick_power"],
        "what": "A circular kick with the instep.",
        "effect": "Mid damage and mid range; the workhorse kick of taekwondo.",
    },
    "back_kick": {
        "action": "BACK_KICK",
        "actuator": "back_kick",
        "params": ["power", "height"],
        "requires": ["kick_power", "precision"],
        "what": "A turning thrust kick with the heel.",
        "effect": "High damage but slow and exhausting; best as a counter.",
    },
    "axe_kick": {
        "action": "AXE_KICK",
        "actuator": "axe_kick",
        "params": ["power", "height"],
        "requires": ["kick_power", "precision"],
        "what": "A rising kick brought down onto the target.",
        "effect": "Very high damage to the head, but slow and easy to read.",
    },
    "punch": {
        "action": "PUNCH",
        "actuator": "punch",
        "params": ["power", "height"],
        "requires": ["kick_speed"],
        "what": "A straight punch to the body or head.",
        "effect": "Fast and cheap but short range; useful in the clinch.",
    },
    "block": {
        "action": "BLOCK",
        "actuator": "block",
        "params": [],
        "requires": ["defense"],
        "what": "Raise a guard to absorb an incoming strike.",
        "effect": "Reduces incoming damage using your defense attribute.",
    },
    "dodge": {
        "action": "DODGE",
        "actuator": "dodge",
        "params": [],
        "requires": ["agility"],
        "what": "Slip out of the way of an incoming strike.",
        "effect": "Can avoid a strike entirely, using your agility attribute.",
    },
}

TOOL_KEYS = list(TOOLS.keys())
TOOL_ACTIONS = {t["action"] for t in TOOLS.values()}


def allowed_actions(tool_ids):
    """Return the action strings for the given tool ids (the permission list)."""
    return [TOOLS[t]["action"] for t in (tool_ids or []) if t in TOOLS]
