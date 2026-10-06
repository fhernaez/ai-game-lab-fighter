"""Brain-level strategy presets (Aggressive / Defensive / Neutral) + admin list.

A **strategy** is a complete game plan: it pre-fills a fighter's *brain* (persona,
goal, skills, tools, model parameters) **and** a *body* attribute allocation per match
difficulty (easy / medium / hard). Each body allocation stays within the point-buy
budget for its difficulty (`body/parameters.py`), so the same strategy works — with a
weaker or stronger body — at any difficulty level.

The three defaults are seeded here; the admin can add more, stored under the
``strategy_presets`` AppSetting.
"""

import copy

from . import skills, tools
from ..body import parameters

DEFAULT_STRATEGIES = {
    "aggressive": {
        "name": "Aggressive",
        "description": "Attack-first: press forward and throw power kicks, high risk.",
        "what": "Play to finish the round fast with heavy strikes.",
        "effect": "Pressures the opponent but costs stamina and leaves openings.",
        "brain": {
            "persona": "A fearless attacker who always looks to land a heavy kick.",
            "goal": "Win the round with a fast, powerful attack.",
            "skills": ["pressure_fighting", "head_hunting"],
            "tools": ["front_kick", "roundhouse_kick", "back_kick", "axe_kick"],
            "params": {"temperature": 0.9},
        },
        "attributes": {
            "easy": {
                "kick_speed": 9, "kick_power": 10, "precision": 6,
                "defense": 2, "agility": 7, "stamina": 5, "reach": 7,
            },
            "medium": {
                "kick_speed": 6, "kick_power": 8, "precision": 4,
                "defense": 1, "agility": 4, "stamina": 3, "reach": 6,
            },
            "hard": {
                "kick_speed": 4, "kick_power": 5, "precision": 2,
                "defense": 1, "agility": 3, "stamina": 2, "reach": 2,
            },
        },
    },
    "defensive": {
        "name": "Defensive",
        "description": "Defense-first: block/dodge everything, counter the error.",
        "what": "Play to make the opponent miss, then punish.",
        "effect": "Longer rounds and fewer hits taken, but less attacking pressure.",
        "brain": {
            "persona": "A patient counter-fighter who never gives away free hits.",
            "goal": "Make the opponent miss, then punish with a kick.",
            "skills": ["counter_attack", "distance_control"],
            "tools": ["retreat", "block", "dodge", "front_kick", "punch"],
            "params": {"temperature": 0.5},
        },
        "attributes": {
            "easy": {
                "kick_speed": 5, "kick_power": 5, "precision": 4,
                "defense": 10, "agility": 8, "stamina": 10, "reach": 4,
            },
            "medium": {
                "kick_speed": 3, "kick_power": 3, "precision": 2,
                "defense": 9, "agility": 5, "stamina": 8, "reach": 2,
            },
            "hard": {
                "kick_speed": 2, "kick_power": 2, "precision": 1,
                "defense": 5, "agility": 3, "stamina": 5, "reach": 1,
            },
        },
    },
    "neutral": {
        "name": "Neutral",
        "description": "Balanced between attack and defense.",
        "what": "Play all-round and choose the best option for each situation.",
        "effect": "Adaptable, without a strong tactical bias.",
        "brain": {
            "persona": "An all-round fighter who reads the opponent and adapts.",
            "goal": "Win the round by choosing the best option.",
            "skills": ["distance_control", "counter_attack", "pressure_fighting"],
            "tools": list(tools.TOOL_KEYS),
            "params": {"temperature": 0.7},
        },
        "attributes": {
            "easy": {
                "kick_speed": 7, "kick_power": 7, "precision": 7,
                "defense": 7, "agility": 7, "stamina": 7, "reach": 7,
            },
            "medium": {
                "kick_speed": 5, "kick_power": 5, "precision": 4,
                "defense": 4, "agility": 5, "stamina": 4, "reach": 4,
            },
            "hard": {
                "kick_speed": 3, "kick_power": 3, "precision": 2,
                "defense": 2, "agility": 3, "stamina": 3, "reach": 2,
            },
        },
    },
}


def default_strategies():
    """A deep copy of the built-in strategy presets (dict keyed by id)."""
    return copy.deepcopy(DEFAULT_STRATEGIES)


def strategy_attributes(strategy, difficulty):
    """The body attribute allocation for ``difficulty``, or None if not defined."""
    attrs = (strategy or {}).get("attributes") or {}
    return attrs.get(difficulty)


def strategy_attributes_cost(strategy, difficulty):
    """Point-buy cost of a strategy's body allocation for a difficulty."""
    attrs = strategy_attributes(strategy, difficulty)
    if not attrs:
        return 0
    return parameters.attributes_cost(attrs)


def apply_strategy(brain, strategy):
    """Return ``brain`` with the strategy's brain fields merged over it.

    The strategy fills persona, goal, skills, tools, and model parameters; the model
    reference, sensors, and memory are left untouched. The body attributes are applied
    separately via :func:`strategy_attributes`.
    """
    brain = dict(brain or {})
    spec = (strategy or {}).get("brain", {}) or {}

    if spec.get("persona") is not None:
        brain["persona"] = spec["persona"]
    if spec.get("goal") is not None:
        brain["goal"] = spec["goal"]
    if spec.get("skills") is not None:
        brain["skills"] = skills.skills_by_ids(spec["skills"]) or skills.load_default_skills()
    if spec.get("tools") is not None:
        brain["tools"] = spec["tools"]

    params = dict(brain.get("params") or {})
    params.update(spec.get("params") or {})
    brain["params"] = params
    return brain
