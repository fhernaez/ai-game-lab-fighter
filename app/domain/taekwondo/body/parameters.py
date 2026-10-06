"""The body: 7 parameters (sliders 1..10) + point-buy + archetypes + what/effect.

A fighter's body is described by **7 numeric attributes**, each a slider from 1 to 10.
Internally the engine maps a slider value to a float ``0.1 .. 1.0`` (``value / 10``).
The point-buy economy charges 1 point for every slider step above the default of 1,
so a fighter can be specialized (a few high values) or balanced (many mid values).

Every attribute carries ``label`` (UI), ``what`` (a short definition) and ``effect``
(what it changes on the fighter), following the platform's auto-explainable rule.
"""

# Each attribute: {label, what, effect}. `what` is the definition, `effect` is the
# cause -> effect on the fighter/game. Both are shown together in the GUI.
ATTRIBUTES = {
    "kick_speed": {
        "label": "Kick Speed",
        "what": "How fast the fighter's strikes land.",
        "effect": "Faster strikes leave the opponent less time to react, raising your hit chance.",
    },
    "kick_power": {
        "label": "Kick Power",
        "what": "How hard the fighter hits.",
        "effect": "Harder strikes deal more damage, but strong kicks also cost more stamina.",
    },
    "precision": {
        "label": "Precision",
        "what": "How accurately the fighter lands the chosen target zone.",
        "effect": "Higher precision makes head shots (more damage) land more reliably.",
    },
    "defense": {
        "label": "Defense",
        "what": "How well the fighter blocks incoming strikes.",
        "effect": "Higher defense means a block removes more incoming damage.",
    },
    "agility": {
        "label": "Agility",
        "what": "Footwork speed and evasion.",
        "effect": "Higher agility moves the fighter faster and makes dodges succeed more often.",
    },
    "stamina": {
        "label": "Stamina",
        "what": "Energy reserves and recovery.",
        "effect": "Higher stamina sustains more attacks and actions; low stamina degrades speed and damage.",
    },
    "reach": {
        "label": "Reach",
        "what": "Effective striking range advantage.",
        "effect": "Longer reach lets the fighter land kicks from further away.",
    },
}

# Convenience lookups derived once from the ATTRIBUTES registry.
ATTRIBUTE_KEYS = list(ATTRIBUTES.keys())
ATTRIBUTE_LABELS = {k: v["label"] for k, v in ATTRIBUTES.items()}
ATTRIBUTE_DESCRIPTIONS = {k: v["what"] for k, v in ATTRIBUTES.items()}
ATTRIBUTE_EFFECTS = {k: v["effect"] for k, v in ATTRIBUTES.items()}

# Slider bounds. Internal float scale is slider / 10 -> 0.1 .. 1.0.
SLIDER_MIN = 1
SLIDER_MAX = 10

# Point-buy budget per difficulty. Each slider point above 1 costs 1 point, so a
# budget of N lets the fighter raise its attributes N steps above their defaults.
DIFFICULTY_BUDGETS = {"easy": 45, "medium": 25, "hard": 12}
# Budget used by the (future) single-player "vs AI" opponent per difficulty.
AI_BUDGETS = {"easy": 12, "medium": 25, "hard": 32}

# Pre-set archetypes: a complete attribute allocation tuned for Medium (25 points).
# They are a quick way to build a recognizable fighting style without moving sliders.
ARCHETYPES = {
    "kicker": {
        "name": "The Kicker (Powerhouse)",
        "description": "Heavy kicks, long reach, slow on the ground.",
        "attributes": {
            "kick_power": 9,
            "reach": 8,
            "precision": 6,
            "kick_speed": 4,
            "stamina": 3,
            "agility": 2,
            "defense": 2,
        },
    },
    "ghost": {
        "name": "The Ghost (Speed Demon)",
        "description": "Covers ground, chains fast kicks, dodges everything.",
        "attributes": {
            "agility": 9,
            "kick_speed": 9,
            "precision": 6,
            "stamina": 3,
            "kick_power": 2,
            "defense": 2,
            "reach": 2,
        },
    },
    "wall": {
        "name": "The Wall (Counter-fighter)",
        "description": "Blocks everything and punishes the opponent's mistakes.",
        "attributes": {
            "defense": 9,
            "stamina": 8,
            "kick_power": 5,
            "agility": 3,
            "kick_speed": 2,
            "precision": 2,
            "reach": 2,
        },
    },
}


def slider_to_float(value):
    """Map a slider value (1..10) to the internal float scale (0.1..1.0)."""
    return max(0.1, min(1.0, value / 10.0))


def default_parameters():
    """All seven attributes at their cheapest default (slider = 1)."""
    return {key: 1 for key in ATTRIBUTE_KEYS}


def clamp_slider(value):
    """Coerce any input into a valid slider int (1..10), defaulting to 1."""
    try:
        return max(SLIDER_MIN, min(SLIDER_MAX, int(value)))
    except (TypeError, ValueError):
        return SLIDER_MIN


def attributes_cost(attributes):
    """Point-buy cost: each slider point above 1 costs 1 point."""
    return sum(max(0, int(attributes.get(k, 1)) - 1) for k in ATTRIBUTE_KEYS)


def team_cost(players):
    """Total point-buy cost across a team's fighters (one per team)."""
    return sum(attributes_cost(p.get("attributes", p.get("parameters", {}))) for p in players)


def difficulty_budget(difficulty):
    """The point-buy budget for a match difficulty."""
    return DIFFICULTY_BUDGETS.get(difficulty, DIFFICULTY_BUDGETS["medium"])


def ai_budget(difficulty):
    return AI_BUDGETS.get(difficulty, AI_BUDGETS["medium"])


def archetype_attributes(archetype_id):
    """Return a full attribute allocation for an archetype id, or None."""
    arch = ARCHETYPES.get(archetype_id)
    if arch is None:
        return None
    merged = default_parameters()
    merged.update(arch["attributes"])
    return merged


def ai_team_attributes(difficulty, rng):
    """Generate a random-but-valid attribute allocation within the AI budget."""
    budget = ai_budget(difficulty)
    attrs = default_parameters()
    while budget > 0:
        key = rng.choice(ATTRIBUTE_KEYS)
        if attrs[key] < SLIDER_MAX:
            attrs[key] += 1
            budget -= 1
    return attrs
