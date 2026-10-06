from app.domain.taekwondo.body import parameters as attributes
from app.domain.taekwondo.core import rules
from app.extensions import db
from app.models import Event, Match, Player, Team, User


def _make_user(username, password="secret"):
    user = User(username=username, email=f"{username}@example.com", role="student")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def test_seed_creates_admin(app):
    with app.app_context():
        assert User.query.filter_by(username="admin").first() is not None


def test_register_and_login(client):
    client.post(
        "/auth/register",
        data={"username": "bob", "email": "bob@example.com", "password": "secret"},
        follow_redirects=True,
    )
    client.get("/auth/logout")
    resp = client.post(
        "/auth/login", data={"username": "bob", "password": "secret"}, follow_redirects=True
    )
    assert b"Matchmaking" in resp.data


def test_fight_rules():
    assert rules.max_health() == 100
    assert rules.rounds_to_win() == 2
    assert rules.home_position(0) == 20.0
    assert rules.home_position(1) == 80.0
    from app.domain.taekwondo.core.world import FightState

    state = FightState()
    state.health = [100, 100]
    state.exchange = 0
    assert rules.is_round_over(state) is False
    state.health = [0, 100]
    assert rules.is_round_over(state) is True
    state.health = [40, 60]
    assert rules.round_winner(state) == 1
    assert rules.is_match_won([2, 0]) is True
    assert rules.is_match_won([1, 1]) is False


def test_attributes_and_budget():
    assert attributes.difficulty_budget("easy") == 45
    assert attributes.difficulty_budget("hard") == 12
    a = {"kick_speed": 8, "kick_power": 1, "precision": 1, "defense": 1,
         "agility": 1, "stamina": 1, "reach": 1}
    assert attributes.attributes_cost(a) == 7
    arch = attributes.archetype_attributes("kicker")
    assert arch["kick_power"] == 9
    assert attributes.slider_to_float(10) == 1.0
    assert attributes.slider_to_float(1) == 0.1


def test_team_config_saves(app, client):
    with app.app_context():
        bob = _make_user("bob")
        alice = _make_user("alice")
        bob_id, alice_id = bob.id, alice.id

    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    client.post("/matchmaking/create", data={"difficulty": "medium"})
    with app.app_context():
        match = Match.query.order_by(Match.id.desc()).first()
        mid = match.id
        team = Team.query.filter_by(match_id=mid, player_id=bob_id).first()
        p = Player.query.filter_by(team_id=team.id, slot=1).first()
        pid = p.id
        # A team now owns exactly one fighter.
        assert Player.query.filter_by(team_id=team.id).count() == 1

    client.post(
        f"/matches/{mid}/team",
        data={
            "strategy": "press and kick",
            f"attr_{pid}_kick_speed": "8",
            f"attr_{pid}_kick_power": "6",
            f"attr_{pid}_precision": "4",
            f"attr_{pid}_defense": "2",
            f"attr_{pid}_agility": "3",
            f"attr_{pid}_stamina": "3",
            f"attr_{pid}_reach": "4",
            f"model_{pid}": "mock:mock-model",
            f"temperature_{pid}": "0.5",
            f"max_tokens_{pid}": "300",
            f"top_p_{pid}": "0.9",
            f"frequency_penalty_{pid}": "0.1",
            f"presence_penalty_{pid}": "0.2",
        },
    )
    with app.app_context():
        p = db.session.get(Player, pid)
        cfg = p.configuration_json
        assert cfg["body"]["parameters"]["kick_speed"] == 8
        assert cfg["brain"]["model"] == "mock:mock-model"
        assert cfg["brain"]["params"]["temperature"] == 0.5


def test_full_match_flow(app, client):
    with app.app_context():
        _make_user("bob")
        _make_user("alice")

    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    client.post("/matchmaking/create", data={"difficulty": "medium"})
    with app.app_context():
        match = Match.query.order_by(Match.id.desc()).first()
        mid = match.id
        assert match.status == "created"

    client.post(f"/matchmaking/{mid}/invite", data={"username": "alice"})
    with app.app_context():
        assert db.session.get(Match, mid).status == "invited"

    client.get("/auth/logout")
    client.post("/auth/login", data={"username": "alice", "password": "secret"})
    client.post(f"/matchmaking/{mid}/accept")
    client.post(f"/matches/{mid}/ready")

    client.get("/auth/logout")
    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    client.post(f"/matches/{mid}/ready")

    with app.app_context():
        match = db.session.get(Match, mid)
        assert match.status == "finished"
        assert match.final_state_json is not None
        types = {e.event_type for e in Event.query.filter_by(match_id=mid).all()}
        assert "DECISION" in types
        assert "HIT" in types
        assert "MATCH_FINISHED" in types


def test_match_delete_cascades(app, client):
    with app.app_context():
        _make_user("bob")
        _make_user("alice")

    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    client.post("/matchmaking/create", data={"difficulty": "easy"})
    with app.app_context():
        mid = Match.query.order_by(Match.id.desc()).first().id
    client.post(f"/matches/{mid}/delete")
    with app.app_context():
        assert db.session.get(Match, mid) is None
        assert Team.query.filter_by(match_id=mid).count() == 0
        assert Event.query.filter_by(match_id=mid).count() == 0


def test_start_match_does_not_reenqueue(app):
    from unittest.mock import patch

    from app.application import match_service
    from app.models import Match

    with app.app_context():
        m = Match(host_id=1, guest_id=2, status="queued", difficulty="medium", seed=1)
        db.session.add(m)
        db.session.commit()
        with patch.object(match_service, "enqueue") as mock_enqueue:
            match_service.start_match(m)
        mock_enqueue.assert_not_called()
        assert m.status == "queued"


def test_engine_streams_events(app):
    from app.domain.taekwondo.body.parameters import default_parameters
    from app.domain.taekwondo.engine import FightEngine
    from app.infrastructure.llm.mock import MockLLMProvider

    collected = []

    def resolve(ref):
        return MockLLMProvider(), "mock-model"

    teams = [
        {"name": f"T{ti}", "instructions": "", "players": [
            {"slot": 1, "name": f"F{ti}", "attributes": {k: 5 for k in default_parameters()}, "brain": {}}
        ]}
        for ti in range(2)
    ]

    engine = FightEngine(teams, resolve, seed=1)
    _events, _state, _usages = engine.run(on_event=collected.append)

    assert len(collected) > 0
    assert collected[0]["event_type"] == "MATCH_STARTED"
    assert any(e["event_type"] == "ATTACK" for e in collected)
    assert any(e["event_type"] == "HIT" for e in collected)
    assert collected[-1]["event_type"] == "MATCH_FINISHED"


def test_engine_deterministic(app):
    from app.domain.taekwondo.body.parameters import default_parameters
    from app.domain.taekwondo.engine import FightEngine
    from app.infrastructure.llm.mock import MockLLMProvider

    def resolve(ref):
        return MockLLMProvider(), "mock-model"

    def run():
        teams = [
            {"name": f"T{ti}", "instructions": "", "players": [
                {"slot": 1, "name": f"F{ti}", "attributes": {k: 5 for k in default_parameters()}, "brain": {}}
            ]}
            for ti in range(2)
        ]
        engine = FightEngine(teams, resolve, seed=42)
        _, state, _ = engine.run()
        return state

    assert run() == run()


def test_core_effective_and_clamp(app):
    from app.application import settings_service

    with app.app_context():
        assert settings_service.get_effective_core()["max_health"] == 100
        settings_service.set_core_overrides({"max_health": "9999"}, {"move_step": "999"})
        eff = settings_service.get_effective_core()
        assert eff["max_health"] == 500  # clamped to max
        assert eff["move_step"] == 30.0  # clamped to max
        settings_service.reset_core()
        assert settings_service.get_effective_core()["max_health"] == 100


def test_rules_honor_core_override():
    from app.domain.taekwondo.core import defaults, rules

    core = defaults.effective_core({"rounds_to_win": 3})
    assert rules.rounds_to_win(core) == 3
    assert rules.is_match_won([3, 0], core) is True
    assert rules.is_match_won([2, 1], core) is False
    assert rules.max_health({"max_health": 200}) == 200


def test_physics_honor_core_override():
    from app.domain.taekwondo.core import defaults, physics

    core = defaults.effective_core({"damage_power_scale": 0.0, "kick_power_scale": 0.0})
    attrs = {"kick_power": 1}
    assert physics.damage("ROUNDHOUSE_KICK", "BODY", 0.0, attrs, 100, core) == 13.0


def test_core_admin_edit_and_restore(app, auth_client):
    from app.application import settings_service

    resp = auth_client.post(
        "/settings/core",
        data={"knob_max_health": "150", "knob_rounds_to_win": "3", "referee_md": "custom referee"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        eff = settings_service.get_effective_core()
        assert eff["max_health"] == 150
        assert eff["rounds_to_win"] == 3
        assert settings_service.get_referee_md() == "custom referee"

    auth_client.post("/settings/core", data={"restore": "1"}, follow_redirects=True)
    with app.app_context():
        assert settings_service.get_effective_core()["max_health"] == 100
        assert settings_service.get_referee_md() != "custom referee"


def test_core_readonly_for_student(app, client):
    with app.app_context():
        _make_user("bob")
    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    resp = client.get("/settings/core")
    assert resp.status_code == 200
    assert b"read-only access" in resp.data


def test_match_snapshots_core_config(app, client):
    with app.app_context():
        _make_user("bob")
        _make_user("alice")
    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    client.post("/matchmaking/create", data={"difficulty": "easy"})
    with app.app_context():
        mid = Match.query.order_by(Match.id.desc()).first().id
    client.post(f"/matchmaking/{mid}/invite", data={"username": "alice"})
    client.get("/auth/logout")
    client.post("/auth/login", data={"username": "alice", "password": "secret"})
    client.post(f"/matchmaking/{mid}/accept")
    client.post(f"/matches/{mid}/ready")
    client.get("/auth/logout")
    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    client.post(f"/matches/{mid}/ready")
    with app.app_context():
        match = db.session.get(Match, mid)
        assert match.status == "finished"
        assert match.core_config_json is not None
        assert match.core_config_json["max_health"] == 100


def test_advanced_view_renders(app, client):
    with app.app_context():
        _make_user("bob")
        _make_user("alice")
    client.post("/auth/login", data={"username": "bob", "password": "secret"})
    client.post("/matchmaking/create", data={"difficulty": "medium"})
    with app.app_context():
        mid = Match.query.order_by(Match.id.desc()).first().id
    resp = client.get(f"/matches/{mid}/advanced")
    assert resp.status_code == 200
    assert b"agent.md" in resp.data
    assert b"body.yaml" in resp.data
    assert b"tools.yaml" in resp.data


def test_agent_and_core_file_render():
    from app.domain.taekwondo.brain import render as br
    from app.domain.taekwondo.core import render as cr

    brain = {
        "persona": "p",
        "goal": "g",
        "task": "t",
        "model": "m",
        "params": {"temperature": 0.7, "max_tokens": 256, "top_p": 1.0,
                   "frequency_penalty": 0.0, "presence_penalty": 0.0},
    }
    md = br.render_agent_md(brain)
    assert "p" in md and "g" in md

    skills_md = br.render_skills_md([{"id": "counter_attack", "title": "Counter-attack", "what": "w", "effect": "e"}])
    assert "Counter-attack" in skills_md and "e" in skills_md

    tools_yaml = br.render_tools_yaml(["roundhouse_kick"])
    assert "roundhouse_kick" in tools_yaml and "ROUNDHOUSE_KICK" in tools_yaml

    body_yaml = br.render_body_yaml({"actuators": ["roundhouse_kick"], "parameters": {"kick_power": 8}})
    assert "kick_power" in body_yaml

    rules_yaml = cr.render_rules_yaml()
    assert "max_health" in rules_yaml
    physics_yaml = cr.render_physics_yaml()
    assert "move_step" in physics_yaml
    assert "referee" in cr.render_referee_md().lower()


def test_brain_permissions_and_prompt():
    from app.domain.taekwondo.brain import decision, tools
    from app.domain.taekwondo.core.world import FightState

    assert tools.allowed_actions(None) == []
    assert tools.allowed_actions(["roundhouse_kick"]) == ["ROUNDHOUSE_KICK"]

    brain = {
        "persona": "P",
        "goal": "G",
        "tools": ["roundhouse_kick"],
        "skills": [{"id": "counter_attack", "title": "Counter-attack", "what": "w", "effect": "e"}],
        "sensors": ["distance"],
        "model": "m",
        "params": {},
    }
    msgs = decision.build_decision_prompt(brain, "T", "Fighter", FightState(), "press the attack", [], 0)
    user = msgs[1]["content"]
    assert "Counter-attack" in user
    assert "roundhouse_kick" in user
    assert "P" in user and "G" in user


def test_what_effect_present():
    from app.domain.taekwondo.body import actuators, parameters
    from app.domain.taekwondo.brain import skills, tools
    from app.domain.taekwondo.core import defaults

    for key, spec in parameters.ATTRIBUTES.items():
        assert spec["what"] and spec["effect"], key
    for key, spec in actuators.ACTUATORS.items():
        assert spec["what"] and spec["effect"], key
    for key, spec in tools.TOOLS.items():
        assert spec["what"] and spec["effect"], key
    for skill in skills.DEFAULT_SKILLS:
        assert skill["what"] and skill["effect"], skill["id"]
    for key, spec in defaults.KNOBS.items():
        assert spec["what"] and spec["effect"], key


def test_prompt_explains_arena():
    from app.domain.taekwondo.brain import decision
    from app.domain.taekwondo.core.world import FightState

    brain = {"persona": "", "goal": "", "tools": [], "skills": [], "sensors": [], "params": {}}
    messages = decision.build_decision_prompt(brain, "T", "Fighter", FightState(), "press the attack", [], 0)
    user = messages[1]["content"]

    assert "ARENA COORDINATES" in user
    assert "distance" in user
    assert "ADVANCE moves you toward the opponent" in user


def test_decision_parse_and_clamp():
    from app.domain.taekwondo.brain import decision

    d = decision.parse_decision({"message": "hi", "move": "JUMP", "action": "BACK_KICK",
                                 "height": "HEAD", "power": 2.0, "distance": -1.0})
    assert d["move"] == "JUMP"
    assert d["action"] == "BACK_KICK"
    assert d["height"] == "HEAD"
    assert d["power"] == 1.0  # clamped
    assert d["distance"] == 0.0  # clamped

    d2 = decision.parse_decision({"action": "NOT_A_MOVE"})
    assert d2["action"] == "FRONT_KICK"  # fallback

    d3 = decision.parse_decision(None)
    assert d3["action"] == "FRONT_KICK"


def test_strategy_presets(app):
    from app.application import settings_service
    from app.domain.taekwondo.body import parameters
    from app.domain.taekwondo.brain import strategies as strategies_mod

    with app.app_context():
        strats = settings_service.get_strategies()
        assert set(strats) >= {"aggressive", "defensive", "neutral"}

        agg = strats["aggressive"]
        assert agg["brain"]["persona"]
        assert "roundhouse_kick" in agg["brain"]["tools"]

        brain = strategies_mod.apply_strategy({}, agg)
        assert brain["persona"] == agg["brain"]["persona"]
        assert brain["tools"] == agg["brain"]["tools"]
        assert brain["params"]["temperature"] == 0.9
        assert brain["skills"]  # resolved to full skill dicts

        for sid in ("aggressive", "defensive", "neutral"):
            strat = strats[sid]
            for difficulty, budget in parameters.DIFFICULTY_BUDGETS.items():
                attrs = strategies_mod.strategy_attributes(strat, difficulty)
                assert attrs is not None, f"{sid} missing {difficulty}"
                assert parameters.attributes_cost(attrs) <= budget, f"{sid} {difficulty} over budget"

        settings_service.set_strategies(
            {"custom": {"name": "Custom", "brain": {"persona": "p", "goal": "g", "skills": [], "tools": ["punch"], "params": {"temperature": 0.3}}}}
        )
        assert "custom" in settings_service.get_strategies()
        settings_service.reset_strategies()
        assert "custom" not in settings_service.get_strategies()


def test_state_events_payload_flattened(app):
    from app.domain.taekwondo.body.parameters import default_parameters
    from app.domain.taekwondo.engine import FightEngine
    from app.infrastructure.llm.mock import MockLLMProvider

    def resolve(ref):
        return MockLLMProvider(), "mock-model"

    teams = [
        {"name": f"T{ti}", "instructions": "", "players": [
            {"slot": 1, "name": f"F{ti}", "attributes": {k: 5 for k in default_parameters()}, "brain": {}}
        ]}
        for ti in range(2)
    ]
    engine = FightEngine(teams, resolve, seed=1)
    events, _, _ = engine.run()

    # State fields must live at payload.* (NOT payload.payload.*), which is what the
    # JS simulator and the interaction log consume.
    started = events[0]
    assert started["event_type"] == "MATCH_STARTED"
    assert isinstance(started["payload"]["rounds_won"], list)
    assert isinstance(started["payload"]["positions"], list)

    round_started = next(e for e in events if e["event_type"] == "ROUND_STARTED")
    assert isinstance(round_started["payload"]["positions"], list)
    assert round_started["payload"]["round"] == 1

    round_won = next(e for e in events if e["event_type"] == "ROUND_WON")
    assert isinstance(round_won["payload"]["winner"], int)
    assert isinstance(round_won["payload"]["rounds_won"], list)

    finished = events[-1]
    assert finished["event_type"] == "MATCH_FINISHED"
    assert isinstance(finished["payload"]["winner"], int)
    assert isinstance(finished["payload"]["rounds_won"], list)
