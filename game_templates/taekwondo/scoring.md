# Scoring

Health-based rounds (no per-strike points): a fighter wins a round by KO or by having
more health at timeout. The fight is won by the first fighter to win 2 rounds.

Strike damage model (see `FIGHTER_SPEC.md` §4):

- `damage = base_damage(action, height) + power * damage_power_scale + kick_power * kick_power_scale`
- **Head** strikes deal more base damage than **body** strikes but are harder to land.
- A successful **block** reduces damage by `block_reduction_base + defense * block_defense_scale`.
- A successful **dodge** avoids the strike entirely.
