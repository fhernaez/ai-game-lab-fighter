"""Core configuration: the tunable rules/combat knobs and their defaults.

Each knob carries ``what`` (a definition) and ``effect`` (what it changes on the
game), plus ``min``/``max``/``step`` for the admin form and ``critical`` to mark
parameters that are dangerous to change. The admin's overrides are stored in
AppSettings and merged over these defaults; a match snapshots the resolved values
at start time so history never changes when the rules change.
"""

KNOBS = {
    # -- rules -------------------------------------------------------------
    "max_health": {
        "group": "rules", "value": 100, "min": 50, "max": 500, "step": 10,
        "what": "Starting health of each fighter.",
        "effect": "Higher health means longer, more forgiving rounds.",
        "critical": True,
    },
    "max_stamina": {
        "group": "rules", "value": 100, "min": 50, "max": 500, "step": 10,
        "what": "Starting stamina of each fighter.",
        "effect": "More stamina lets a fighter attack and act longer before gassing out.",
        "critical": True,
    },
    "rounds_to_win": {
        "group": "rules", "value": 2, "min": 1, "max": 5, "step": 1,
        "what": "Rounds needed to win the fight (best-of).",
        "effect": "A higher target makes the fight longer and rewards consistency.",
        "critical": True,
    },
    "max_rounds": {
        "group": "rules", "value": 3, "min": 1, "max": 9, "step": 1,
        "what": "Maximum number of rounds in a fight.",
        "effect": "Caps the total length of the fight.",
        "critical": True,
    },
    "max_exchanges": {
        "group": "rules", "value": 30, "min": 5, "max": 100, "step": 1,
        "what": "Exchange cap before a round is decided by remaining health.",
        "effect": "A lower cap forces quicker decisions and more aggressive play.",
        "critical": False,
    },

    # -- physics -----------------------------------------------------------
    "move_step": {
        "group": "physics", "value": 8.0, "min": 1.0, "max": 30.0, "step": 1.0,
        "what": "Base footwork step length on the arena.",
        "effect": "A longer step closes or opens distance faster.",
        "critical": False,
    },
    "move_agility_scale": {
        "group": "physics", "value": 8.0, "min": 0.0, "max": 20.0, "step": 1.0,
        "what": "Extra step length gained at max agility.",
        "effect": "Larger scale rewards high Agility with faster footwork.",
        "critical": False,
    },
    "damage_power_scale": {
        "group": "physics", "value": 8.0, "min": 0.0, "max": 30.0, "step": 1.0,
        "what": "Damage added at full attack power.",
        "effect": "Larger scale makes max-power strikes much heavier.",
        "critical": False,
    },
    "kick_power_scale": {
        "group": "physics", "value": 6.0, "min": 0.0, "max": 30.0, "step": 1.0,
        "what": "Damage added at max Kick Power attribute.",
        "effect": "Larger scale makes the Kick Power attribute matter more.",
        "critical": False,
    },
    "head_hit_penalty": {
        "group": "physics", "value": 0.15, "min": 0.0, "max": 0.5, "step": 0.01,
        "what": "Hit-chance penalty for targeting the head.",
        "effect": "Larger penalty makes head shots riskier but they still deal more damage.",
        "critical": False,
    },
    "hit_base": {
        "group": "physics", "value": 0.55, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Base chance a strike connects.",
        "effect": "Higher base means more strikes land overall.",
        "critical": False,
    },
    "hit_speed_scale": {
        "group": "physics", "value": 0.25, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Hit-chance bonus at max Kick Speed.",
        "effect": "Larger bonus rewards fast kicks.",
        "critical": False,
    },
    "hit_agility_scale": {
        "group": "physics", "value": 0.25, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Hit-chance penalty from the defender's max Agility.",
        "effect": "Larger penalty makes agile defenders harder to hit.",
        "critical": False,
    },
    "block_reduction_base": {
        "group": "physics", "value": 0.35, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Base fraction of damage removed by a block.",
        "effect": "Higher base makes blocks reduce more damage for everyone.",
        "critical": False,
    },
    "block_defense_scale": {
        "group": "physics", "value": 0.40, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Extra block reduction at max Defense.",
        "effect": "Larger scale makes the Defense attribute matter more.",
        "critical": False,
    },
    "dodge_base": {
        "group": "physics", "value": 0.20, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Base chance a dodge avoids a strike.",
        "effect": "Higher base makes dodging safer for everyone.",
        "critical": False,
    },
    "dodge_agility_scale": {
        "group": "physics", "value": 0.35, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Extra dodge chance at max Agility.",
        "effect": "Larger scale rewards agile dodgers.",
        "critical": False,
    },
    "jump_dodge_bonus": {
        "group": "physics", "value": 0.25, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Dodge-chance bonus for jumping.",
        "effect": "Jumping makes a fighter harder to hit this exchange.",
        "critical": False,
    },
    "stamina_attack_base": {
        "group": "physics", "value": 8.0, "min": 0.0, "max": 40.0, "step": 1.0,
        "what": "Base stamina cost of an attack.",
        "effect": "Higher cost makes attacking more exhausting.",
        "critical": False,
    },
    "stamina_move_cost": {
        "group": "physics", "value": 4.0, "min": 0.0, "max": 40.0, "step": 1.0,
        "what": "Stamina cost of moving (advance/retreat/jump).",
        "effect": "Higher cost makes constant movement exhausting.",
        "critical": False,
    },
    "stamina_recovery": {
        "group": "physics", "value": 6.0, "min": 0.0, "max": 40.0, "step": 1.0,
        "what": "Stamina recovered each exchange.",
        "effect": "Higher recovery lets a fighter keep pressing without gassing out.",
        "critical": False,
    },
    "stamina_penalty": {
        "group": "physics", "value": 0.25, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Hit/damage penalty at zero stamina.",
        "effect": "Larger penalty makes an exhausted fighter miss more and hit softer.",
        "critical": False,
    },
    "reach_scale": {
        "group": "physics", "value": 0.10, "min": 0.0, "max": 1.0, "step": 0.01,
        "what": "Fraction by which Reach extends effective striking range.",
        "effect": "Larger scale makes the Reach attribute matter more.",
        "critical": False,
    },
}

# Flattened default values, one per knob.
DEFAULTS = {key: spec["value"] for key, spec in KNOBS.items()}

REFEREE_MD = """# The Referee (deterministic)

The referee is **not an LLM**. It is a small piece of deterministic code that
applies the rules and combat to every exchange:

1. **Rounds** — a fight is best-of-3 (first to win 2 rounds). Each round starts both
   fighters at full health and stamina, and resets the exchange counter.
2. **Exchanges** — both fighters decide simultaneously. Each moves (advance / retreat
   / jump / hold) and then performs an action (a kick, punch, block, or dodge).
3. **Combat** — the core checks the strike's range, then whether it connects (Kick
   Speed vs the defender's Agility, penalized for head shots), then whether the
   defender blocks (Defense reduces damage) or dodges (Agility may avoid it entirely).
   Damage scales with power and Kick Power; every action costs stamina.
4. **Round end** — a fighter is KO'd at 0 health, or the exchange cap is reached and
   the fighter with more health wins (ties go to more damage dealt, then team 0).
5. **Win** — the first fighter to win the required number of rounds wins the fight.

All randomness is seeded per match, so a run is reproducible.
"""


def _clamp(key, value):
    """Clamp/coerce a knob override to its allowed range and type."""
    spec = KNOBS[key]
    try:
        value = float(value)
    except (TypeError, ValueError):
        return spec["value"]
    value = max(spec["min"], min(spec["max"], value))
    if isinstance(spec["value"], int):
        value = int(round(value))
    return value


def effective_core(overrides=None):
    """Return DEFAULTS merged with validated/clamped overrides."""
    core = dict(DEFAULTS)
    for key, value in (overrides or {}).items():
        if key in KNOBS:
            core[key] = _clamp(key, value)
    return core
