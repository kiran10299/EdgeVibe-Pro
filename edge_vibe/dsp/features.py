import numpy as np
from typing import Dict, Any

class TimeDomainFeatures:
    """Computes standard vibration and mechanical wear time-domain metrics."""

    @staticmethod
    def extract(signal: np.ndarray) -> Dict[str, float]:
        signal = np.asarray(signal, dtype=np.float64)
        if len(signal) == 0:
            return {
                "mean": 0.0, "rms": 0.0, "peak": 0.0, "pk_pk": 0.0,
                "crest_factor": 1.0, "kurtosis": 3.0, "std": 0.0
            }

        mean = float(np.mean(signal))
        std = float(np.std(signal))
        peak = float(np.max(np.abs(signal)))
        pk_pk = float(np.ptp(signal))

        # Root Mean Square (RMS)
        rms = float(np.sqrt(np.mean(signal ** 2)))

        # Crest Factor: Peak / RMS
        crest_factor = float(peak / rms) if rms > 1e-6 else 1.0

        # Kurtosis (Normalized 4th central moment, Gaussian noise = 3.0)
        if std > 1e-6:
            kurtosis = float(np.mean((signal - mean) ** 4) / (std ** 4))
        else:
            kurtosis = 3.0

        return {
            "mean": mean,
            "std": std,
            "rms": rms,
            "peak": peak,
            "pk_pk": pk_pk,
            "crest_factor": crest_factor,
            "kurtosis": kurtosis,
        }
