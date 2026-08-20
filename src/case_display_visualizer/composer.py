"""Turns raw sensor samples into smoothed energy values for scenes to consume."""

from __future__ import annotations

from dataclasses import dataclass, field

from case_display_visualizer.sensors.base import Sensor

# Smoothing is asymmetric: react quickly to spikes (attack) but settle down
# slowly (decay), so visuals feel punchy without being jittery.
ATTACK_RATE = 8.0  # per second
DECAY_RATE = 1.5  # per second


@dataclass
class EnergyState:
    values: dict[str, float] = field(default_factory=dict)

    def get(self, name: str, default: float = 0.0) -> float:
        return self.values.get(name, default)

    @property
    def overall(self) -> float:
        if not self.values:
            return 0.0
        return max(self.values.values())


class Composer:
    """Samples a set of sensors each tick and smooths their output."""

    def __init__(self, sensors: list[Sensor]) -> None:
        self._sensors = sensors
        self._smoothed: dict[str, float] = {s.name: 0.0 for s in sensors}

    def update(self, dt: float) -> EnergyState:
        for sensor in self._sensors:
            raw = _safe_sample(sensor)
            current = self._smoothed[sensor.name]
            rate = ATTACK_RATE if raw > current else DECAY_RATE
            blend = min(1.0, rate * dt)
            self._smoothed[sensor.name] = current + (raw - current) * blend

        return EnergyState(values=dict(self._smoothed))


def _safe_sample(sensor: Sensor) -> float:
    try:
        return max(0.0, min(1.0, sensor.sample()))
    except Exception:
        return 0.0
