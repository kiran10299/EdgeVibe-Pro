import pytest
import numpy as np
from edge_vibe.dsp.features import TimeDomainFeatures
from edge_vibe.dsp.spectral import SpectralAnalyzer
from edge_vibe.diagnostics.iso10816 import Iso10816Standard, IsoZone

def test_time_domain_features():
    # Pure sine wave with amp = 1.0 -> RMS = 1 / sqrt(2) ≈ 0.707
    t = np.linspace(0, 1.0, 1000, endpoint=False)
    sig = np.sin(2 * np.pi * 50.0 * t)
    feats = TimeDomainFeatures.extract(sig)

    assert 0.70 < feats["rms"] < 0.72
    assert 0.99 < feats["peak"] < 1.01
    assert 1.99 < feats["pk_pk"] < 2.01
    assert 1.39 < feats["crest_factor"] < 1.43

def test_spectral_analyzer():
    # 60 Hz sine wave
    fs = 1000
    t = np.arange(1000) / fs
    sig = 2.5 * np.sin(2 * np.pi * 60.0 * t)

    analyzer = SpectralAnalyzer(sample_rate_hz=fs)
    peak_f, peak_amp = analyzer.get_peak_frequency(sig)

    assert 59.0 <= peak_f <= 61.0
    assert 2.3 < peak_amp < 2.7

def test_iso_10816_zones():
    good = Iso10816Standard.evaluate(1.1)
    assert good["zone"] == "ZONE_A"
    assert good["severity"] == "GOOD"

    warn = Iso10816Standard.evaluate(3.5)
    assert warn["zone"] == "ZONE_C"
    assert warn["severity"] == "WARNING"

    trip = Iso10816Standard.evaluate(5.2)
    assert trip["zone"] == "ZONE_D"
    assert trip["is_trip"] is True
