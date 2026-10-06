# Game: Taekwondo Fighter

A 1v1 taekwondo fight between two AI fighters on a one-dimensional arena.

- **Teams:** exactly 2, one fighter each.
- **Win:** best of 3 rounds (first to win 2). A round ends by KO (health ≤ 0) or
  timeout (the exchange cap); the higher remaining health wins, ties broken by damage
  dealt.
- **Exchange:** both fighters decide simultaneously (move + action), then the
  deterministic core resolves range, hit chance, block/dodge, damage, and stamina.

See `rules.md`, `scoring.md`, and `referee.md`.
