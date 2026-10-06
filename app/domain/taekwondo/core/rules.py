"""Taekwondo rules: arena, round win, KO, timeout, match win.

All functions accept an optional ``core`` dict (the resolved core configuration, see
``defaults.py``). When omitted they fall back to the defaults, so existing callers and
tests keep working unchanged.
"""

from . import defaults

# The arena is a 1D line from 0 to 100. Fighters occupy scalar positions on it.
ARENA_MIN = 0.0
ARENA_MAX = 100.0

# Starting positions: red (team 0) on the left, blue (team 1) on the right.
HOME_POSITIONS = {0: 20.0, 1: 80.0}


def _c(core):
    return core or defaults.DEFAULTS


def arena_length(core=None):
    return ARENA_MAX


def home_position(team_index):
    return HOME_POSITIONS.get(team_index, 20.0)


def max_health(core=None):
    return _c(core)["max_health"]


def max_stamina(core=None):
    return _c(core)["max_stamina"]


def rounds_to_win(core=None):
    return _c(core)["rounds_to_win"]


def max_rounds(core=None):
    return _c(core)["max_rounds"]


def max_exchanges(core=None):
    return _c(core)["max_exchanges"]


def is_round_over(state, core=None):
    """A round ends by KO (health <= 0) or timeout (exchange cap reached)."""
    return state.health[0] <= 0 or state.health[1] <= 0 or state.exchange >= max_exchanges(core)


def round_winner(state, core=None):
    """Determine the round winner from health, then damage dealt, then team 0.

    Returns 0 (red) or 1 (blue).
    """
    h0, h1 = state.health
    if h0 != h1:
        return 0 if h0 > h1 else 1
    # Tie on health: whoever dealt more damage this round wins.
    d0, d1 = state.damage_dealt
    if d0 != d1:
        return 0 if d0 > d1 else 1
    # Still tied: team 0 (red) wins.
    return 0


def is_match_won(rounds_won, core=None):
    """Whether either fighter has enough round wins to take the fight."""
    target = rounds_to_win(core)
    return rounds_won[0] >= target or rounds_won[1] >= target
