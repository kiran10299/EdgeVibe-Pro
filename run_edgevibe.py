#!/usr/bin/env python3
"""EdgeVibe-Pro: Industrial Multi-Sensor Edge DAQ & Predictive Condition Monitoring Daemon.
Author: Kiran Shivakumar
"""

import sys
import os
import time
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from edge_vibe.daq.acquisition import DaqWorker
from edge_vibe.dsp.features import TimeDomainFeatures
from edge_vibe.dsp.spectral import SpectralAnalyzer
from edge_vibe.diagnostics.iso10816 import Iso10816Standard
from edge_vibe.diagnostics.alarm_manager import AlarmManager
from edge_vibe.gateway.modbus_publisher import ModbusHoldingRegisterMap
from edge_vibe.gateway.logger import TimeSeriesLogger

import sys

# Enable UTF-8 encoding support on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

class Color:
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def render_ascii_spectrum(freqs: np.ndarray, amps: np.ndarray, num_bins: int = 14) -> str:
    """Renders small horizontal ASCII bar chart of the FFT magnitude spectrum."""
    if len(amps) == 0:
        return "No spectral data"

    # Group into frequency bands up to 250 Hz
    max_f = 250.0
    valid_mask = freqs <= max_f
    f_sub = freqs[valid_mask]
    a_sub = amps[valid_mask]

    if len(a_sub) == 0:
        return ""

    bin_edges = np.linspace(0, max_f, num_bins + 1)
    bars = []
    max_amp = max(0.01, float(np.max(a_sub)))

    for i in range(num_bins):
        mask = (f_sub >= bin_edges[i]) & (f_sub < bin_edges[i+1])
        b_amp = np.max(a_sub[mask]) if np.any(mask) else 0.0
        bar_len = int((b_amp / max_amp) * 12)
        bar_str = "#" * bar_len + "-" * (12 - bar_len)
        f_mid = int((bin_edges[i] + bin_edges[i+1]) / 2)
        bars.append(f"{f_mid:>3}Hz: [{bar_str}]")

    return " | ".join(bars[:5]) + "\n" + " | ".join(bars[5:10])

def main():
    print(f"{Color.CYAN}Initializing EdgeVibe-Pro Industrial Condition Monitoring Platform...{Color.RESET}")

    # 1. Initialize Subsystems
    sample_rate = 1000
    window_size = 512
    daq = DaqWorker(sample_rate_hz=sample_rate, buffer_capacity=10000)
    analyzer = SpectralAnalyzer(sample_rate_hz=sample_rate)
    alarm_mgr = AlarmManager()
    modbus = ModbusHoldingRegisterMap()
    db_logger = TimeSeriesLogger("edgevibe_telemetry.db")

    # Start DAQ Worker Thread
    daq.start()
    print(f"DAQ Worker Thread started ({sample_rate} Hz, 4 Synchronized Channels).")
    print(f"Press [1]: Normal Machine | [2]: Moderate Bearing Wear | [3]: Critical Fault | [Q]: Exit\n")

    iteration = 0
    fault_state = 0.0

    try:
        while True:
            time.sleep(0.5)  # 2 Hz telemetry refresh rate
            iteration += 1

            # Fetch latest data window from RingBuffer
            data_window = daq.ring_buffer.get_latest(window_size)
            if data_window.shape[0] < window_size:
                continue

            ch_vibe = data_window[:, 0]
            ch_ae = data_window[:, 1]
            ch_temp = data_window[:, 2]
            ch_force = data_window[:, 3]

            # 2. Digital Signal Processing (DSP)
            vibe_features = TimeDomainFeatures.extract(ch_vibe)
            ae_features = TimeDomainFeatures.extract(ch_ae)
            freqs, amps = analyzer.compute_fft(ch_vibe)
            peak_freq, peak_amp = analyzer.get_peak_frequency(ch_vibe)

            curr_temp = float(np.mean(ch_temp))
            curr_force = float(np.mean(ch_force))

            # 3. ISO 10816-3 Severity Evaluation
            # Standard calculates RMS velocity in mm/s
            vibe_rms = vibe_features["rms"] * 2.2  # Scaled to velocity mm/s
            iso_result = Iso10816Standard.evaluate(vibe_rms)

            # 4. Alarm & Interlock Management
            active_alarms = alarm_mgr.evaluate_telemetry(
                vibe_rms=vibe_rms,
                kurtosis=vibe_features["kurtosis"],
                temp_c=curr_temp
            )

            # 5. Gateway Modbus Register Update & Database Logging
            modbus.update_telemetry(
                features=vibe_features,
                peak_freq=peak_freq,
                temp_c=curr_temp,
                force_n=curr_force,
                is_trip=iso_result["is_trip"]
            )
            db_logger.log_record(
                features=vibe_features,
                peak_freq=peak_freq,
                temp_c=curr_temp,
                force_n=curr_force,
                iso_zone=iso_result["zone"],
                is_trip=iso_result["is_trip"]
            )

            # 6. Render Terminal Telemetry Dashboard
            zone_color = Color.GREEN if iso_result["severity"] == "GOOD" else (
                Color.CYAN if iso_result["severity"] == "ACCEPTABLE" else (
                    Color.YELLOW if iso_result["severity"] == "WARNING" else Color.RED
                )
            )

            os.system("cls" if os.name == "nt" else "clear")
            print(f"{Color.CYAN}{'='*78}{Color.RESET}")
            print(f"{Color.BOLD}EdgeVibe-Pro | Industrial Edge DAQ & Condition Monitoring Daemon{Color.RESET}")
            print(f"ISO 10816-3 Status : {zone_color}{Color.BOLD}{iso_result['zone_description']}{Color.RESET}")
            print(f"{Color.CYAN}{'='*78}{Color.RESET}")

            # Telemetry Metrics
            print(f"\n{Color.BOLD}TIME-DOMAIN VIBRATION METRICS (Ch 0):{Color.RESET}")
            print(f"  RMS Velocity   : {zone_color}{vibe_rms:.3f} mm/s{Color.RESET}  (Zone Limit: {Iso10816Standard.LIMIT_B_TO_C} mm/s)")
            print(f"  Peak Amplitude : {vibe_features['peak']:.3f} mm/s")
            print(f"  Peak-to-Peak   : {vibe_features['pk_pk']:.3f} mm/s")
            print(f"  Crest Factor   : {vibe_features['crest_factor']:.2f}")
            print(f"  Kurtosis       : {vibe_features['kurtosis']:.2f}  (> 5.0 indicates bearing micro-pitting)")

            print(f"\n{Color.BOLD}MULTI-SENSOR TELEMETRY:{Color.RESET}")
            print(f"  Acoustic Emission : {ae_features['rms']*100:.2f} mV RMS")
            print(f"  Bearing Temp      : {curr_temp:.1f} deg C")
            print(f"  Normal Load Force : {curr_force:.1f} N")
            print(f"  Dominant Peak     : {peak_freq:.1f} Hz (Amp: {peak_amp:.3f})")

            # ASCII Spectrum
            print(f"\n{Color.BOLD}FFT VIBRATION SPECTRUM BANDS (0 - 250 Hz):{Color.RESET}")
            print(render_ascii_spectrum(freqs, amps))

            # Modbus Holding Registers
            regs = modbus.read_holding_registers(0, 8)
            print(f"\n{Color.BOLD}MODBUS HOLDING REGISTERS (PLC Gateway 40001 - 40008):{Color.RESET}")
            print(f"  [40001..40008]: {regs}")

            # Relay Interlock State
            if alarm_mgr.relay_interlock_tripped:
                print(f"\n{Color.RED}{Color.BOLD}[EMERGENCY INTERLOCK TRIPPED] RELAY DISCONNECTED: {iso_result['recommended_action']}{Color.RESET}")
            else:
                print(f"\n{Color.GREEN}[RELAY STATUS: ARMED & RUNNING]{Color.RESET}")

            print(f"\n{Color.CYAN}Telemetry logged to 'edgevibe_telemetry.db'. Press Ctrl+C to terminate.{Color.RESET}")

            # Cycle fault severity automatically every 6 iterations if unattended, or keep nominal
            if iteration == 8:
                print("\n[Simulation] Demonstrating Bearing Wear Injection...")
                daq.set_fault_severity(0.45)
            elif iteration == 16:
                print("\n[Simulation] Demonstrating Severe Bearing Pitting Fault...")
                daq.set_fault_severity(0.95)
            elif iteration == 24:
                break

    except KeyboardInterrupt:
        pass
    finally:
        daq.stop()
        print("\nDAQ Worker stopped cleanly.")

if __name__ == "__main__":
    main()
