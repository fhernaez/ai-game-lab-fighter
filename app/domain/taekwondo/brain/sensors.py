"""Sensors: what the brain may read (the perception / sandbox boundary)."""

SENSORS = ["distance", "own_health", "own_stamina", "own_attributes", "fight_history", "score"]

SENSOR_LABELS = {
    "distance": "Distance to the opponent",
    "own_health": "Your own health",
    "own_stamina": "Your own stamina",
    "own_attributes": "Your own body parameters",
    "fight_history": "What has happened this round",
    "score": "Rounds won and current round",
}


def render_sensors(sensors):
    return ", ".join(sensors or SENSORS)
