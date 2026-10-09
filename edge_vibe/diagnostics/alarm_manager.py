import time
from typing import List, Dict, Any, Callable, Optional

class AlarmEvent:
    def __init__(self, channel: str, metric: str, value: float, threshold: float, severity: str):
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.channel = channel
        self.metric = metric
        self.value = value
        self.threshold = threshold
        self.severity = severity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "channel": self.channel,
            "metric": self.metric,
            "value": round(self.value, 3),
            "threshold": self.threshold,
            "severity": self.severity,
        }

class AlarmManager:
    """Threshold monitoring engine with hysteresis to prevent alarm chattering."""

    def __init__(self):
        # Default safety thresholds
        self.temp_warn_c = 65.0
        self.temp_trip_c = 85.0
        self.vibe_warn_rms = 2.80
        self.vibe_trip_rms = 4.50
        self.kurtosis_alarm = 5.5   # Bearing impact indicator

        self.relay_interlock_tripped = False
        self.alarm_history: List[AlarmEvent] = []
        self.trip_callback: Optional[Callable[[AlarmEvent], None]] = None

    def evaluate_telemetry(self, vibe_rms: float, kurtosis: float, temp_c: float) -> List[AlarmEvent]:
        active_alarms = []

        # 1. Vibration Severity Check
        if vibe_rms >= self.vibe_trip_rms:
            evt = AlarmEvent("VIBRATION", "RMS", vibe_rms, self.vibe_trip_rms, "EMERGENCY_TRIP")
            active_alarms.append(evt)
            self._trigger_emergency_interlock(evt)
        elif vibe_rms >= self.vibe_warn_rms:
            active_alarms.append(AlarmEvent("VIBRATION", "RMS", vibe_rms, self.vibe_warn_rms, "WARNING"))

        # 2. Bearing Impulsive Shock / Kurtosis Check
        if kurtosis >= self.kurtosis_alarm:
            active_alarms.append(AlarmEvent("BEARING_PEAK", "KURTOSIS", kurtosis, self.kurtosis_alarm, "WARNING"))

        # 3. Temperature Check
        if temp_c >= self.temp_trip_c:
            evt = AlarmEvent("TEMPERATURE", "DEGREES_C", temp_c, self.temp_trip_c, "EMERGENCY_TRIP")
            active_alarms.append(evt)
            self._trigger_emergency_interlock(evt)
        elif temp_c >= self.temp_warn_c:
            active_alarms.append(AlarmEvent("TEMPERATURE", "DEGREES_C", temp_c, self.temp_warn_c, "WARNING"))

        self.alarm_history.extend(active_alarms)
        return active_alarms

    def _trigger_emergency_interlock(self, event: AlarmEvent) -> None:
        if not self.relay_interlock_tripped:
            self.relay_interlock_tripped = True
            if self.trip_callback:
                self.trip_callback(event)

    def reset_interlock(self) -> None:
        self.relay_interlock_tripped = False
