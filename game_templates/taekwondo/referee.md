# The Referee (deterministic)

The referee is **not an LLM**. It is deterministic code that applies the rules and
combat to every exchange:

1. Resolve footwork (advance / retreat / jump / hold) and recompute distance.
2. Range check: an out-of-reach strike misses.
3. Hit chance: raised by the attacker's Kick Speed, lowered by the defender's Agility
   and by targeting the head.
4. Defense: a block reduces damage (Defense); a dodge may avoid it (Agility).
5. Damage and stamina: apply damage, charge stamina costs, and recover.
6. Round end: KO or timeout; score the round and check the best-of-3 win condition.

All randomness is seeded per match.
