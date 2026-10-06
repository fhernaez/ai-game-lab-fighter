"""Event type constants for the taekwondo interaction log.

The engine emits one event per step of an exchange (movement, attack, hit, etc.).
Each event is a plain dict ``{"event_type", "actor_id", "payload"}`` produced by
:func:`make_event`; the application layer persists them incrementally so the live
view and the graphical simulation can replay the fight in real time.
"""

# Match / round lifecycle ------------------------------------------------------
MATCH_STARTED = "MATCH_STARTED"
ROUND_STARTED = "ROUND_STARTED"
EXCHANGE_STARTED = "EXCHANGE_STARTED"
ROUND_WON = "ROUND_WON"
MATCH_FINISHED = "MATCH_FINISHED"

# Per-exchange actions ----------------------------------------------------------
# DECISION is emitted once per fighter per exchange with the full trace (prompt,
# model, params, raw + parsed decision, attributes).
DECISION = "DECISION"
# MOVEMENT records a fighter's footwork (advance / retreat / jump / hold).
MOVEMENT = "MOVEMENT"
# ATTACK records an attack attempt and its result ("hit" | "miss" | "dodged").
ATTACK = "ATTACK"
# HIT / BLOCK / DODGE record how the defender resolved an incoming strike.
HIT = "HIT"
BLOCK = "BLOCK"
DODGE = "DODGE"
# DAMAGE / STAMINA record the numeric consequences of an exchange.
DAMAGE = "DAMAGE"
STAMINA = "STAMINA"


def make_event(event_type, actor_id=None, **payload):
    """Build one event dict with a uniform shape."""
    return {"event_type": event_type, "actor_id": actor_id, "payload": payload}
