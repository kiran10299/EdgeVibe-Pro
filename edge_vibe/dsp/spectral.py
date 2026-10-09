import numpy as np
from typing import Tuple, Dict, Any

class SpectralAnalyzer:
    """Computes Fast Fourier Transform (FFT) and Power Spectral Density (PSD)."""

    def __init__(self, sample_rate_hz: int = 1000):
        self.fs = sample_rate_hz

    def compute_fft(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Computes one-sided amplitude spectrum with Hanning windowing."""
        signal = np.asarray(signal, dtype=np.float64)
        n = len(signal)
        if n < 4:
            return np.array([]), np.array([])

        # Hanning window to suppress side-lobes
        window = np.hanning(n)
        windowed_sig = (signal - np.mean(signal)) * window

        # Compute FFT
        fft_vals = np.fft.rfft(windowed_sig)
        freqs = np.fft.rfftfreq(n, d=1.0 / self.fs)

        # Scale amplitude (preserving energy)
        amps = (2.0 / np.sum(window)) * np.abs(fft_vals)

        return freqs, amps

    def get_peak_frequency(self, signal: np.ndarray) -> Tuple[float, float]:
        """Returns (peak_freq_hz, peak_amplitude)."""
        freqs, amps = self.compute_fft(signal)
        if len(amps) == 0:
            return 0.0, 0.0
        # Exclude DC offset (< 2 Hz)
        valid_idx = np.where(freqs >= 2.0)[0]
        if len(valid_idx) == 0:
            return 0.0, 0.0

        idx = valid_idx[np.argmax(amps[valid_idx])]
        return float(freqs[idx]), float(amps[idx])

    def get_band_power(self, signal: np.ndarray, low_hz: float, high_hz: float) -> float:
        """Calculates integrated spectral energy within a specified frequency band."""
        freqs, amps = self.compute_fft(signal)
        if len(amps) == 0:
            return 0.0
        mask = (freqs >= low_hz) & (freqs <= high_hz)
        return float(np.sum(amps[mask] ** 2))
