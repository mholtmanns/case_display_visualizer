"""Common interface for sensors that produce a normalized 0..1 reading."""

from __future__ import annotations

from typing import Protocol


class Sensor(Protocol):
    name: str

    def sample(self) -> float:
        """Return the current reading, normalized to 0.0..1.0."""
