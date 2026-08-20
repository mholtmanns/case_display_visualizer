"""Desktop audio (WASAPI loopback) sensor with FFT band extraction.

Captures whatever is playing through the default output device (not the
microphone) on a background thread, and exposes both an overall energy
level (for the Sensor protocol / composer) and a set of frequency-band
magnitudes for an equalizer-style visual.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import pyaudiowpatch as pyaudio
except ImportError:  # pragma: no cover - optional dependency
    pyaudio = None

CHUNK_SIZE = 1024
# Auto-gain: normalize band magnitudes against a slowly decaying running
# peak, so visuals stay lively at both quiet and loud system volume.
GAIN_DECAY = 0.995
MIN_GAIN_CEILING = 1.0


class AudioSensor:
    name = "audio"

    def __init__(self, band_count: int = 32) -> None:
        self.band_count = band_count
        self._bands = np.zeros(band_count, dtype=np.float32)
        self._overall = 0.0
        self._lock = threading.Lock()
        self._gain_ceiling = MIN_GAIN_CEILING
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._pa = None
        self._stream = None
        self._sample_rate = 48000

        if pyaudio is None:
            logger.info("PyAudioWPatch not installed; audio sensor disabled")
            return

        try:
            self._pa = pyaudio.PyAudio()
            device = self._find_loopback_device(self._pa)
            self._sample_rate = int(device["defaultSampleRate"])
            self._stream = self._pa.open(
                format=pyaudio.paFloat32,
                channels=device["maxInputChannels"],
                rate=self._sample_rate,
                frames_per_buffer=CHUNK_SIZE,
                input=True,
                input_device_index=device["index"],
            )
            self._channels = device["maxInputChannels"]
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        except Exception as exc:  # pragma: no cover - depends on hardware
            logger.info("No audio loopback device available; disabled (%s)", exc)
            self._stream = None

    @staticmethod
    def _find_loopback_device(pa) -> dict:
        try:
            return pa.get_device_info_by_index(pa.get_default_wasapi_loopback())
        except Exception:
            wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = pa.get_device_info_by_index(
                wasapi_info["defaultOutputDevice"]
            )
            if not default_speakers.get("isLoopbackDevice"):
                for loopback in pa.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        return loopback
                raise RuntimeError("No matching loopback device found")
            return default_speakers

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                raw = self._stream.read(CHUNK_SIZE, exception_on_overflow=False)
            except Exception as exc:  # pragma: no cover - depends on hardware
                logger.warning("Audio read failed: %s", exc)
                continue

            samples = np.frombuffer(raw, dtype=np.float32)
            if self._channels > 1:
                samples = samples.reshape(-1, self._channels).mean(axis=1)

            self._process(samples)

    def _process(self, samples: np.ndarray) -> None:
        overall = float(np.sqrt(np.mean(samples**2))) if samples.size else 0.0

        windowed = samples * np.hanning(len(samples))
        spectrum = np.abs(np.fft.rfft(windowed))

        band_magnitudes = _bucket_log_bands(spectrum, self._sample_rate, self.band_count)

        peak = float(band_magnitudes.max()) if band_magnitudes.size else 0.0
        self._gain_ceiling = max(peak, self._gain_ceiling * GAIN_DECAY, MIN_GAIN_CEILING)
        normalized = np.clip(band_magnitudes / self._gain_ceiling, 0.0, 1.0)

        with self._lock:
            self._overall = min(1.0, overall * 4.0)
            self._bands = normalized.astype(np.float32)

    def sample(self) -> float:
        with self._lock:
            return self._overall

    def get_bands(self) -> np.ndarray:
        with self._lock:
            return self._bands.copy()

    def close(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa is not None:
            self._pa.terminate()


def _bucket_log_bands(spectrum: np.ndarray, sample_rate: int, band_count: int) -> np.ndarray:
    """Group linear FFT bins into log-spaced bands (like a classic EQ)."""
    n_bins = len(spectrum)
    if n_bins == 0:
        return np.zeros(band_count, dtype=np.float32)

    min_freq, max_freq = 30.0, sample_rate / 2.0
    edges = np.logspace(np.log10(min_freq), np.log10(max_freq), band_count + 1)
    freqs = np.fft.rfftfreq(2 * (n_bins - 1), d=1.0 / sample_rate)

    bands = np.zeros(band_count, dtype=np.float32)
    for i in range(band_count):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if mask.any():
            bands[i] = spectrum[mask].mean()
    return bands
