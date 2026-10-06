"""The fighter body: parameters + actuators + position/health/stamina.

This is a thin, deterministic entity. The match engine holds the *authoritative*
fight state in ``core/world.py`` (so it can be replayed from the event log); this
class is the conceptual "body" an advanced student reads about in the Advanced view.
"""

from . import actuators, parameters


class Body:
    def __init__(self, parameters_dict=None, actuators_list=None):
        self.parameters = parameters_dict or parameters.default_parameters()
        self.actuators = actuators_list or actuators.ACTUATOR_KEYS
        # The fighter's position on the 1D arena (x in 0..100).
        self.position = 20.0

    def can(self, actuator):
        """Whether this body knows the given actuator (move)."""
        return actuator in self.actuators

    def param(self, key):
        """Read one attribute slider value (defaulting to 1)."""
        return self.parameters.get(key, 1)
