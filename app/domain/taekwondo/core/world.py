"""The world / environment: the fight state and scoreboard.

``FightState`` is the single source of truth the engine mutates and the event log
replays. It is intentionally a plain, serializable object: ``to_dict()`` is what the
graphical simulation and the interaction log consume.
"""

from . import defaults, rules


class FightState:
    def __init__(self):
        self.health = [defaults.DEFAULTS["max_health"], defaults.DEFAULTS["max_health"]]
        self.stamina = [defaults.DEFAULTS["max_stamina"], defaults.DEFAULTS["max_stamina"]]
        # Scalar positions on the 1D arena (red left, blue right).
        self.positions = [rules.home_position(0), rules.home_position(1)]
        self.rounds_won = [0, 0]
        self.current_round = 1
        self.exchange = 0
        # Total damage each fighter dealt this round (used to break ties).
        self.damage_dealt = [0.0, 0.0]
        self.round_history = []  # short-term memory strings for this round
        self.round_history_sets = []  # per-round snapshot (unused by engine, kept for API)
        self.winner = None

    def distance(self):
        """Distance between the two fighters on the arena."""
        return abs(self.positions[0] - self.positions[1])

    def to_dict(self):
        return {
            "rounds_won": list(self.rounds_won),
            "current_round": self.current_round,
            "exchange": self.exchange,
            "health": list(self.health),
            "stamina": list(self.stamina),
            "positions": list(self.positions),
            "distance": self.distance(),
            "damage_dealt": list(self.damage_dealt),
            "winner": self.winner,
        }
