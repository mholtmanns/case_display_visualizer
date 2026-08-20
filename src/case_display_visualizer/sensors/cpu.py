"""CPU utilization sensor."""

from __future__ import annotations

import psutil


class CpuSensor:
    name = "cpu"

    def __init__(self) -> None:
        # Prime psutil's internal measurement window so the first real
        # sample() call isn't a meaningless 0.0.
        psutil.cpu_percent(interval=None)

    def sample(self) -> float:
        return psutil.cpu_percent(interval=None) / 100.0
