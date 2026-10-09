from enum import Enum
from typing import Dict, Any

class IsoZone(Enum):
    ZONE_A = "ZONE_A (Good / Newly Commissioned)"
    ZONE_B = "ZONE_B (Acceptable / Continuous Operation)"
    ZONE_C = "ZONE_C (Unsatisfactory / Maintenance Required)"
    ZONE_D = "ZONE_D (Unacceptable / Critical Damage Risk)"

class Iso10816Standard:
    """Evaluates Vibration Severity according to ISO 10816-3 (Industrial Machines)."""

    # Velocity limits in mm/s RMS for Class II (Medium Machines, 15kW - 300kW, Rigid Foundation)
    LIMIT_A_TO_B = 1.40  # < 1.4 mm/s = Good
    LIMIT_B_TO_C = 2.80  # 1.4 - 2.8 mm/s = Acceptable
    LIMIT_C_TO_D = 4.50  # 2.8 - 4.5 mm/s = Unsatisfactory, > 4.5 = Danger

    @classmethod
    def evaluate(cls, velocity_rms_mms: float) -> Dict[str, Any]:
        v = float(velocity_rms_mms)

        if v < cls.LIMIT_A_TO_B:
            zone = IsoZone.ZONE_A
            severity = "GOOD"
            color = "#22c55e"  # Green
            action = "Machine operating in optimal baseline condition."
        elif v < cls.LIMIT_B_TO_C:
            zone = IsoZone.ZONE_B
            severity = "ACCEPTABLE"
            color = "#38bdf8"  # Cyan
            action = "Machine eligible for unrestricted long-term operation."
        elif v < cls.LIMIT_C_TO_D:
            zone = IsoZone.ZONE_C
            severity = "WARNING"
            color = "#f59e0b"  # Amber
            action = "Vibration elevated. Schedule bearing inspection / balance check."
        else:
            zone = IsoZone.ZONE_D
            severity = "CRITICAL_TRIP"
            color = "#ef4444"  # Red
            action = "EXCEEDED SAFETY THRESHOLD! Immediate shutdown recommended."

        return {
            "velocity_rms_mms": v,
            "zone": zone.name,
            "zone_description": zone.value,
            "severity": severity,
            "color": color,
            "recommended_action": action,
            "is_trip": (zone == IsoZone.ZONE_D)
        }
