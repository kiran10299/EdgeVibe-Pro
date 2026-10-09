import numpy as np
import math
import time
import random

class IndustrialSignalGenerator:
    """Simulates realistic multi-channel sensor signals from an industrial rotating machine."""

    def __init__(self, sample_rate_hz: int = 1000):
        self.fs = sample_rate_hz
        self.time_offset = 0.0
        self.shaft_freq_hz = 29.5     # ~1770 RPM motor
        self.bearing_bpfi_hz = 147.5   # Ball Pass Frequency Inner race (~5X shaft)
        self.ambient_temp_c = 28.0
        self.nominal_load_n = 250.0
        self.degradation_factor = 0.0  # 0.0 = brand new, 1.0 = severe bearing fault

    def set_fault_severity(self, factor: float) -> None:
        """Inject simulated bearing wear / misalignment (0.0 to 1.0)."""
        self.degradation_factor = max(0.0, min(1.0, float(factor)))

    def generate_chunk(self, num_samples: int) -> np.ndarray:
        """Generates synchronized 4-channel data chunk:
        Ch 0: Vibration Acceleration (g / mm/s^2)
        Ch 1: Acoustic Emission (mV)
        Ch 2: Bearing Temperature (°C)
        Ch 3: Normal Tribological Force (N)
        """
        t = np.arange(num_samples) / self.fs + self.time_offset
        self.time_offset += num_samples / self.fs

        deg = self.degradation_factor

        # 1. Vibration Channel (Fundamental 1X + Harmonic 2X + Bearing BPFI + Noise)
        # Baseline 1X unbalance
        vibe_1x = (0.35 + 0.8 * deg) * np.sin(2 * np.pi * self.shaft_freq_hz * t)
        vibe_2x = (0.12 + 0.4 * deg) * np.sin(2 * np.pi * (2 * self.shaft_freq_hz) * t + 0.5)
        # Inner race bearing impact fault pulses
        bpfi_impacts = (1.8 * deg) * np.sin(2 * np.pi * self.bearing_bpfi_hz * t) * (np.sin(2 * np.pi * self.shaft_freq_hz * t) ** 4)
        noise_vibe = np.random.normal(0, 0.08, num_samples)
        ch_vibe = vibe_1x + vibe_2x + bpfi_impacts + noise_vibe

        # 2. Acoustic Emission Channel (High-frequency transient bursts)
        ae_carrier = np.sin(2 * np.pi * 320.0 * t) * (0.05 + 0.45 * deg)
        ae_bursts = np.where(np.random.rand(num_samples) > (0.98 - 0.05 * deg), np.random.uniform(1.2, 4.5, num_samples) * deg, 0.0)
        ch_ae = ae_carrier + ae_bursts + np.random.normal(0, 0.02, num_samples)

        # 3. Bearing Temperature Channel (Creeps up with degradation)
        temp_rise = 18.0 * deg + (self.time_offset * 0.02)
        ch_temp = np.full(num_samples, self.ambient_temp_c + temp_rise) + np.random.normal(0, 0.05, num_samples)

        # 4. Tribology Load Force Channel
        ch_force = np.full(num_samples, self.nominal_load_n) + np.sin(2 * np.pi * 0.5 * t) * 12.0 + np.random.normal(0, 1.5, num_samples)

        return np.column_stack((ch_vibe, ch_ae, ch_temp, ch_force))
