"""GPU utilization sensor (NVIDIA only, via nvidia-ml-py).

Degrades gracefully to a constant 0.0 reading if no NVIDIA GPU/driver is
present, so the app still runs on AMD/Intel-only machines.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    import pynvml
except ImportError:  # pragma: no cover - optional dependency
    pynvml = None


class GpuSensor:
    name = "gpu"

    def __init__(self) -> None:
        self._handle = None
        if pynvml is None:
            logger.info("nvidia-ml-py not installed; GPU sensor disabled")
            return
        try:
            pynvml.nvmlInit()
            self._handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        except Exception as exc:  # pragma: no cover - depends on hardware
            logger.info("No NVIDIA GPU detected; GPU sensor disabled (%s)", exc)
            self._handle = None

    def sample(self) -> float:
        if self._handle is None:
            return 0.0
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self._handle)
            return util.gpu / 100.0
        except Exception as exc:  # pragma: no cover - depends on hardware
            logger.warning("GPU sample failed: %s", exc)
            return 0.0
