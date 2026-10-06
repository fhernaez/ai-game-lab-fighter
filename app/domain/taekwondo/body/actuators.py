"""The body's move library (actuators).

An **actuator** is a physical movement the fighter can perform. There are two kinds:

- **Footwork** — advance, retreat, jump (and the passive "hold"). These change the
  fighter's position or stance; they are always available (movement is a body
  capability, not a permission-gated tool).
- **Techniques** — the kicks, punch, block, and dodge. These are wired to the brain
  through the tool registry (`brain/tools.py`), which is the permission boundary: the
  brain may only choose a technique whose tool is in its `tools` list.

Each actuator carries ``what`` (definition) and ``effect`` (what it changes), for the
auto-explainable GUI and the Advanced view.
"""

ACTUATORS = {
    "advance": {
        "what": "Step forward toward the opponent.",
        "effect": "Closes the distance so your kicks are in range. Uses agility for step length.",
    },
    "retreat": {
        "what": "Step backward away from the opponent.",
        "effect": "Opens the distance to escape attacks and reset the engagement.",
    },
    "jump": {
        "what": "Leap off the mat.",
        "effect": "Raises the chance to evade low attacks this exchange, at a stamina cost.",
    },
    "front_kick": {
        "what": "A straight snap kick with the ball of the foot (Ap Chagi).",
        "effect": "Fast and cheap; low damage. A good tool to keep the opponent honest.",
    },
    "roundhouse_kick": {
        "what": "A circular kick with the instep (Dollyo Chagi).",
        "effect": "Mid damage and mid range; the workhorse kick of taekwondo.",
    },
    "back_kick": {
        "what": "A turning thrust kick with the heel (Dwi Chagi).",
        "effect": "High damage but slow and exhausting; best as a counter.",
    },
    "axe_kick": {
        "what": "A rising kick brought down onto the target (Naeryo Chagi).",
        "effect": "Very high damage to the head, but slow and easy to read.",
    },
    "punch": {
        "what": "A straight punch to the body or head (Jireugi).",
        "effect": "Fast and cheap but short range; useful in the clinch.",
    },
    "block": {
        "what": "Raise a guard to absorb an incoming strike.",
        "effect": "Reduces incoming damage using your defense attribute.",
    },
    "dodge": {
        "what": "Slip out of the way of an incoming strike.",
        "effect": "Can avoid a strike entirely, using your agility attribute.",
    },
}

ACTUATOR_KEYS = list(ACTUATORS.keys())
