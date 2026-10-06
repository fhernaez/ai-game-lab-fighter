"""Deterministic combat core for taekwondo.

The core resolves each exchange: footwork (positions), attack range, hit chance,
block/dodge, damage, and stamina. All randomness uses a seeded ``random.Random`` so a
fight is reproducible.

The tunable constants come from the resolved ``core`` config (see ``core/defaults.py``);
each function accepts an optional ``core`` dict and falls back to the defaults. The
per-technique *shape* (range, base damage, stamina) is fixed in ``TECHNIQUES`` below.
"""

from . import defaults, rules
from ..body.parameters import slider_to_float


# Per-technique constants. `range` is the effective reach on the arena; `body` and
# `head` are base damages; `stamina` is the extra stamina cost; `speed` is a hit
# multiplier that models how telegraphed the strike is (1.0 = fast, lower = slow).
TECHNIQUES = {
    "PUNCH":            {"range": 10.0, "body": 5,  "head": 8,  "stamina": 6,  "speed": 1.0},
    "FRONT_KICK":       {"range": 14.0, "body": 9,  "head": 13, "stamina": 9,  "speed": 0.9},
    "ROUNDHOUSE_KICK":  {"range": 16.0, "body": 13, "head": 19, "stamina": 12, "speed": 0.8},
    "BACK_KICK":        {"range": 18.0, "body": 19, "head": 27, "stamina": 18, "speed": 0.6},
    "AXE_KICK":         {"range": 15.0, "body": 11, "head": 24, "stamina": 15, "speed": 0.65},
}

# The actions that count as attacks (the rest are defense / footwork).
ATTACK_ACTIONS = set(TECHNIQUES.keys())
DEFENSE_ACTIONS = {"BLOCK", "DODGE"}
MOVE_ACTIONS = {"ADVANCE", "RETREAT", "JUMP", "HOLD"}


def _f(attrs, key):
    """Read an attribute as a 0.1..1.0 float (slider -> internal scale)."""
    return slider_to_float(attrs.get(key, 1))


def _c(core):
    return core or defaults.DEFAULTS


def move_step(attrs, core=None):
    """Footwork step length (arena units) from agility."""
    c = _c(core)
    return c["move_step"] + c["move_agility_scale"] * _f(attrs, "agility")


def attack_range(action, attrs, core=None):
    """Effective striking range for a technique, scaled by reach."""
    c = _c(core)
    base = TECHNIQUES[action]["range"]
    return base * (1.0 + c["reach_scale"] * _f(attrs, "reach"))


def _stamina_ratio(stamina, core):
    """0..1 fraction of max stamina remaining (clamped)."""
    return max(0.0, min(1.0, stamina / max(1.0, _c(core)["max_stamina"])))


def hit_chance(action, height, att_attrs, def_attrs, att_stamina, core=None):
    """Probability (0..1) a strike connects, clamped to [0.05, 0.95].

    Raised by the attacker's kick_speed, lowered by the defender's agility and by
    targeting the HEAD (harder). An exhausted attacker (low stamina) misses more.
    """
    c = _c(core)
    base = c["hit_base"]
    base += c["hit_speed_scale"] * _f(att_attrs, "kick_speed")
    base -= c["hit_agility_scale"] * _f(def_attrs, "agility")
    if height == "HEAD":
        base -= c["head_hit_penalty"]
    base -= c["stamina_penalty"] * (1.0 - _stamina_ratio(att_stamina, core))
    # `speed` scales the effective chance: slow, telegraphed strikes connect less.
    base *= TECHNIQUES[action]["speed"]
    return max(0.05, min(0.95, base))


def dodge_chance(def_attrs, move, core=None):
    """Probability (0..1) a DODGE avoids an incoming strike."""
    c = _c(core)
    chance = c["dodge_base"] + c["dodge_agility_scale"] * _f(def_attrs, "agility")
    if move == "JUMP":
        chance += c["jump_dodge_bonus"]
    return max(0.0, min(1.0, chance))


def block_reduction(def_attrs, core=None):
    """Fraction (0..1) of incoming damage removed by a block."""
    c = _c(core)
    return max(0.0, min(0.95, c["block_reduction_base"] + c["block_defense_scale"] * _f(def_attrs, "defense")))


def base_damage(action, height, core=None):
    """Base damage of a technique at the given target zone (before power/attributes)."""
    return TECHNIQUES[action]["head" if height == "HEAD" else "body"]


def damage(action, height, power, att_attrs, att_stamina, core=None):
    """Total damage of a landed strike (>= 1).

    = base_damage + power * damage_power_scale + kick_power * kick_power_scale,
    reduced by the stamina penalty for an exhausted attacker.
    """
    c = _c(core)
    power = max(0.0, min(1.0, power))
    total = base_damage(action, height, core)
    total += power * c["damage_power_scale"]
    total += _f(att_attrs, "kick_power") * c["kick_power_scale"]
    total *= 1.0 - c["stamina_penalty"] * (1.0 - _stamina_ratio(att_stamina, core))
    return max(1.0, total)


def stamina_cost(move, action, core=None):
    """Stamina spent in one exchange (movement + technique)."""
    c = _c(core)
    cost = 0.0
    if move in ("ADVANCE", "RETREAT", "JUMP"):
        cost += c["stamina_move_cost"]
    if action in ATTACK_ACTIONS:
        cost += c["stamina_attack_base"] + TECHNIQUES[action]["stamina"]
    elif action in DEFENSE_ACTIONS:
        cost += c["stamina_attack_base"] * 0.5
    return cost
