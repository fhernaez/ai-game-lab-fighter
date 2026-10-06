"""Skills: the playbook (what the fighter knows), rendered into the prompt."""

DEFAULT_SKILLS = [
    {
        "id": "distance_control",
        "title": "Distance control",
        "what": "Manage the gap: stay just outside the opponent's reach, strike when in range.",
        "effect": "Lets you hit without being hit; frustrates aggressive opponents.",
    },
    {
        "id": "counter_attack",
        "title": "Counter-attack",
        "what": "Bait the opponent's attack, block or dodge it, then punish with a kick.",
        "effect": "Turns the opponent's aggression into openings for high-damage counters.",
    },
    {
        "id": "head_hunting",
        "title": "Head hunting",
        "what": "Aim kicks at the head for maximum damage, accepting the extra risk.",
        "effect": "Bigger damage per hit, but head shots are harder to land.",
    },
    {
        "id": "pressure_fighting",
        "title": "Pressure fighting",
        "what": "Advance and chain kicks to keep the opponent on the back foot.",
        "effect": "Wins exchanges on tempo, but costs stamina and leaves you open.",
    },
]


def render_skills(skills):
    """Render a list of skills into a prompt block."""
    if not skills:
        return "(no skills)"
    return "\n".join(
        f"- {s.get('title', s.get('id', 'skill'))}: {s.get('what', '')}" for s in skills
    )


def load_default_skills():
    return [dict(s) for s in DEFAULT_SKILLS]


def skills_by_ids(ids):
    """Return the full skill dicts for the given skill ids (order-preserving)."""
    if not ids:
        return []
    by_id = {s["id"]: s for s in DEFAULT_SKILLS}
    return [dict(by_id[i]) for i in ids if i in by_id]
