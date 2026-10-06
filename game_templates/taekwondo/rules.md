# Rules

1. The arena is a 1D line `x ∈ [0, 100]`. Red starts at `x = 20`, blue at `x = 80`.
2. Distance is `|x_red − x_blue|`. "Advance" always moves toward the opponent,
   "retreat" always away.
3. A round starts with health 100 and stamina 100 for both fighters.
4. A round ends by **KO** (health ≤ 0) or **timeout** (the exchange cap). On timeout,
   higher health wins; ties go to more damage dealt, then team 0.
5. The fight is **best of 3** (first to win 2 rounds).
6. All randomness is seeded per match, so a run is reproducible.
