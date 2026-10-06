"""FightEngine: an exchange-based, message-driven taekwondo fight.

Each round is a series of **exchanges**. In every exchange both fighters decide
simultaneously: they move (advance / retreat / jump / hold) and act (a kick, punch,
block, or dodge). The deterministic core resolves range, hit chance, block/dodge,
damage, and stamina, and the engine emits the event stream. A round ends by KO or
timeout; the fight is best-of-3 rounds.
"""

import random

from . import events as ev
from .brain import decision as decisions
from .brain import tools as brain_tools
from .core import defaults, physics, rules
from .core.world import FightState


class MatchCancelled(Exception):
    pass


def _state_payload(state, **extra):
    """Flatten a FightState into one event payload plus optional extra keys.

    Event consumers (the JS simulator and the interaction log) read state fields
    DIRECTLY at ``payload.<field>`` — e.g. ``payload.rounds_won``, ``payload.positions``,
    ``payload.health``, ``payload.stamina``, ``payload.current_round``, ``payload.winner``.
    So we must NOT wrap the state a second time. ``extra`` (e.g. ``round=…``,
    ``winner=…``) is merged last so it overrides any same-named key in the state.
    """
    payload = state.to_dict()
    payload.update(extra)
    return payload


class _EventSink(list):
    """A list that also forwards each appended event to an optional callback.

    Lets the caller persist/stream events live as the fight produces them.
    """

    def __init__(self, on_event=None):
        super().__init__()
        self.on_event = on_event

    def append(self, item):
        super().append(item)
        if self.on_event:
            self.on_event(item)


class FightEngine:
    def __init__(self, teams, resolve, seed=0, core=None):
        self.teams = teams
        self.resolve = resolve      # resolve(model_ref) -> (provider, model)
        self.core = core or defaults.DEFAULTS
        self.rng = random.Random(seed)

    # -- helpers -----------------------------------------------------------
    def _player(self, team_index):
        # A team owns exactly one fighter (slot 1).
        return self.teams[team_index]["players"][0]

    def _attrs(self, team_index):
        return self._player(team_index).get("attributes", {})

    def _action_hint(self, team_index, state):
        """A short tactical hint that becomes the brain's `task` for the exchange."""
        if state.distance() > 30:
            return "close the distance"
        if state.health[team_index] < state.health[1 - team_index]:
            return "defend and look for a counter"
        return "press the attack"

    # -- match loop ---------------------------------------------------------
    def run(self, on_event=None, should_stop=None):
        events = _EventSink(on_event)
        usages = []
        state = FightState()

        events.append(ev.make_event(ev.MATCH_STARTED, **_state_payload(state)))

        for _round in range(1, rules.max_rounds(self.core) + 1):
            if state.winner is not None:
                break
            state.current_round = _round
            state.health = [float(rules.max_health(self.core)), float(rules.max_health(self.core))]
            state.stamina = [float(rules.max_stamina(self.core)), float(rules.max_stamina(self.core))]
            state.positions = [rules.home_position(0), rules.home_position(1)]
            state.exchange = 0
            state.damage_dealt = [0.0, 0.0]
            state.round_history = []

            events.append(ev.make_event(ev.ROUND_STARTED, **_state_payload(state, round=_round)))

            while not rules.is_round_over(state, self.core):
                if should_stop and should_stop():
                    raise MatchCancelled()
                events.append(ev.make_event(ev.EXCHANGE_STARTED, **_state_payload(state)))
                self._play_exchange(state, events, usages)

            winner = rules.round_winner(state, self.core)
            state.rounds_won[winner] += 1
            events.append(ev.make_event(ev.ROUND_WON, **_state_payload(state, round=_round, winner=winner)))
            if rules.is_match_won(state.rounds_won, self.core):
                state.winner = winner

        state.winner = 0 if state.rounds_won[0] > state.rounds_won[1] else 1
        events.append(ev.make_event(ev.MATCH_FINISHED, **_state_payload(state)))
        return events, state.to_dict(), usages

    # -- one exchange -------------------------------------------------------
    def _play_exchange(self, state, events, usages):
        # 1. Both fighters decide simultaneously (each gets the shared round history).
        fighter_decisions = []
        for ti in range(2):
            player = self._player(ti)
            hint = self._action_hint(ti, state)
            d, _ = self._decide(ti, player, hint, state, events, usages, state.round_history)
            fighter_decisions.append(d)
            state.round_history.append(f"[{player['name']}] {d['message']}")

        # 2. Apply footwork and recompute distance.
        for ti in range(2):
            self._apply_move(ti, fighter_decisions[ti]["move"], state, events)

        # 3. Resolve each fighter's attack (if any) against the other.
        for ti in range(2):
            action = fighter_decisions[ti]["action"]
            if action in physics.ATTACK_ACTIONS:
                self._resolve_attack(ti, 1 - ti, fighter_decisions[ti], fighter_decisions[1 - ti], state, events)

        # 4. Stamina costs + recovery.
        self._apply_stamina(state, fighter_decisions, events)

        state.exchange += 1

    def _apply_move(self, team_index, move, state, events):
        """Apply a fighter's footwork to its arena position.

        "Advance" always moves *toward* the opponent and "retreat" moves *away*,
        regardless of which fighter is currently on the left, so the fighters can
        never drift apart by passing each other.
        """
        attrs = self._attrs(team_index)
        step = physics.move_step(attrs, self.core)
        own = state.positions[team_index]
        opp = state.positions[1 - team_index]
        direction = 1 if opp > own else -1
        delta = 0.0
        if move == "ADVANCE":
            delta = direction * step
        elif move == "RETREAT":
            delta = -direction * step
        old = state.positions[team_index]
        new = max(rules.ARENA_MIN, min(rules.ARENA_MAX, old + delta))
        state.positions[team_index] = new
        events.append(
            ev.make_event(ev.MOVEMENT, team=team_index, move=move,
                          from_pos=round(old, 2), to_pos=round(new, 2))
        )

    def _resolve_attack(self, attacker, defender, att_decision, def_decision, state, events):
        """Resolve one fighter's strike against the other.

        Sequence: range check -> hit chance -> dodge -> block -> damage.
        """
        attrs_a = self._attrs(attacker)
        attrs_d = self._attrs(defender)
        action = att_decision["action"]
        height = att_decision["height"]
        power = att_decision["power"]
        distance = state.distance()

        # Range check: out of reach => automatic miss.
        rng = physics.attack_range(action, attrs_a, self.core)
        if distance > rng:
            events.append(ev.make_event(
                ev.ATTACK, team=attacker, action=action, height=height,
                result="miss", reason="out_of_range", distance=round(distance, 2)))
            return

        # Hit chance: does the strike connect?
        hit = physics.hit_chance(action, height, attrs_a, attrs_d, state.stamina[attacker], self.core)
        if self.rng.random() > hit:
            events.append(ev.make_event(
                ev.ATTACK, team=attacker, action=action, height=height,
                result="miss", reason="evaded", distance=round(distance, 2)))
            return

        # Dodge: the defender may avoid the strike entirely. The attacker's kick still
        # plays (ATTACK first), then the defender evades (DODGE).
        if def_decision["action"] == "DODGE":
            dodge = physics.dodge_chance(attrs_d, def_decision["move"], self.core)
            if self.rng.random() < dodge:
                events.append(ev.make_event(
                    ev.ATTACK, team=attacker, action=action, height=height, result="dodged"))
                events.append(ev.make_event(ev.DODGE, team=defender))
                return

        # Hit: ATTACK (the kick) first, then the defender's block (if any), then the
        # HIT reaction and the DAMAGE applied.
        damage = physics.damage(action, height, power, attrs_a, state.stamina[attacker], self.core)
        events.append(ev.make_event(
            ev.ATTACK, team=attacker, action=action, height=height,
            result="hit", damage=round(damage, 1), distance=round(distance, 2)))
        if def_decision["action"] == "BLOCK":
            reduction = physics.block_reduction(attrs_d, self.core)
            damage = max(1.0, damage * (1.0 - reduction))
            events.append(ev.make_event(ev.BLOCK, team=defender, reduction=round(reduction, 2)))

        state.health[defender] = max(0.0, state.health[defender] - damage)
        state.damage_dealt[attacker] += damage

        events.append(ev.make_event(ev.HIT, team=defender, damage=round(damage, 1)))
        events.append(ev.make_event(
            ev.DAMAGE, team=defender, damage=round(damage, 1), health=round(state.health[defender], 1)))

    def _apply_stamina(self, state, fighter_decisions, events):
        """Charge stamina for each fighter's move/action, then recover."""
        for ti in range(2):
            cost = physics.stamina_cost(fighter_decisions[ti]["move"], fighter_decisions[ti]["action"], self.core)
            stamina = state.stamina[ti] - cost + self.core["stamina_recovery"]
            stamina = max(0.0, min(float(self.core["max_stamina"]), stamina))
            state.stamina[ti] = stamina
            events.append(ev.make_event(
                ev.STAMINA, team=ti, cost=round(cost, 1), stamina=round(stamina, 1)))

    # -- decision -----------------------------------------------------------
    def _decide(self, team_index, player, action_hint, state, events, usages, round_history):
        brain = player.get("brain") or {}
        provider, model = self.resolve(brain.get("model") or player.get("model") or "")
        messages = decisions.build_decision_prompt(
            brain, self.teams[team_index]["name"], player["name"],
            state, action_hint, round_history, team_index
        )
        fallback = self._fallback_decision(team_index, state)

        error = None
        raw = ""
        tokens_in = tokens_out = 0
        model_used = model
        try:
            result = provider.complete(
                messages, model=model, mock_output=fallback, **brain.get("params", {})
            )
            parsed = result.parse_json(default=fallback)
            decision = decisions.parse_decision(parsed, fallback=fallback)
            raw = result.content
            tokens_in = result.tokens_input
            tokens_out = result.tokens_output
            model_used = result.model or model
        except Exception as exc:
            # A single failed LLM call must not crash the fight: fall back to the
            # deterministic decision and record the error for the interaction log.
            decision = dict(fallback)
            error = str(exc)

        # Tool permission check: the action must be one the agent's tools allow.
        allowed = brain_tools.allowed_actions(brain.get("tools")) or list(decisions.ACTIONS)
        if decision["action"] not in allowed:
            decision["action"] = allowed[0]

        events.append(
            ev.make_event(
                ev.DECISION,
                actor_id=player["name"],
                team=team_index,
                team_name=self.teams[team_index]["name"],
                slot=player.get("slot", 1),
                action_hint=action_hint,
                message=decision.get("message", ""),
                move=decision["move"],
                action=decision["action"],
                height=decision["height"],
                power=decision["power"],
                distance=decision["distance"],
                prompt=messages,
                model=model_used,
                params=brain.get("params", {}),
                attributes=player.get("attributes", {}),
                raw=raw,
                parsed=decision,
                error=error,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
            )
        )
        usages.append(
            {"member_id": player["name"], "tokens_input": tokens_in, "tokens_output": tokens_out, "model": model_used}
        )
        return decision, error

    def _fallback_decision(self, team_index, state):
        """A deterministic, valid decision used when the LLM is absent or errors."""
        distance = state.distance()
        power = self.rng.uniform(0.4, 0.9)
        if distance > 30:
            return {"message": "I close the distance.", "move": "ADVANCE", "action": "FRONT_KICK",
                    "height": "BODY", "power": power, "distance": 0.4}
        if state.health[team_index] < state.health[1 - team_index]:
            return {"message": "I defend and wait for an opening.", "move": "HOLD", "action": "BLOCK",
                    "height": "BODY", "power": 0.3, "distance": 0.5}
        height = "HEAD" if self.rng.random() < 0.3 else "BODY"
        return {"message": "I strike with a roundhouse kick.", "move": "ADVANCE", "action": "ROUNDHOUSE_KICK",
                "height": height, "power": power, "distance": 0.3}
