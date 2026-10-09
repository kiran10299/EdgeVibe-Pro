from typing import Dict, Any

class ModbusHoldingRegisterMap:
    """Simulates Industrial Modbus Holding Registers (40001 - 40008) for PLC/SCADA integration."""

    # Register Addresses (0-indexed offset)
    REG_VIBE_RMS_MMS_X100   = 0   # Reg 40001: Vibration RMS (mm/s * 100)
    REG_VIBE_PEAK_MMS_X100  = 1   # Reg 40002: Vibration Peak (mm/s * 100)
    REG_KURTOSIS_X10        = 2   # Reg 40003: Bearing Kurtosis (* 10)
    REG_CREST_FACTOR_X10    = 3   # Reg 40004: Crest Factor (* 10)
    REG_PEAK_FREQ_HZ        = 4   # Reg 40005: Dominant Peak Frequency (Hz)
    REG_TEMP_DEG_C_X10      = 5   # Reg 40006: Bearing Temp (°C * 10)
    REG_FORCE_NEWTONS       = 6   # Reg 40007: Tribology Load Force (N)
    REG_ALARM_STATUS_WORD   = 7   # Reg 40008: Bit 0=Warn, Bit 1=Trip, Bit 2=Relay

    def __init__(self):
        self.registers = [0] * 8

    def update_telemetry(self, features: Dict[str, Any], peak_freq: float, temp_c: float, force_n: float, is_trip: bool) -> None:
        vibe_rms = features.get("rms", 0.0)
        vibe_peak = features.get("peak", 0.0)
        kurtosis = features.get("kurtosis", 3.0)
        crest_factor = features.get("crest_factor", 1.0)

        # Scale float values to integer 16-bit unsigned registers
        self.registers[self.REG_VIBE_RMS_MMS_X100] = min(65535, max(0, int(vibe_rms * 100)))
        self.registers[self.REG_VIBE_PEAK_MMS_X100] = min(65535, max(0, int(vibe_peak * 100)))
        self.registers[self.REG_KURTOSIS_X10] = min(65535, max(0, int(kurtosis * 10)))
        self.registers[self.REG_CREST_FACTOR_X10] = min(65535, max(0, int(crest_factor * 10)))
        self.registers[self.REG_PEAK_FREQ_HZ] = min(65535, max(0, int(peak_freq)))
        self.registers[self.REG_TEMP_DEG_C_X10] = min(65535, max(0, int(temp_c * 10)))
        self.registers[self.REG_FORCE_NEWTONS] = min(65535, max(0, int(force_n)))

        # Status word bitmask
        status_word = 0
        if vibe_rms > 2.8:
            status_word |= (1 << 0)  # Warning bit
        if is_trip:
            status_word |= (1 << 1)  # Trip bit
            status_word |= (1 << 2)  # Relay open bit
        self.registers[self.REG_ALARM_STATUS_WORD] = status_word

    def read_holding_registers(self, start_addr: int = 0, count: int = 8) -> list:
        end = min(len(self.registers), start_addr + count)
        return self.registers[start_addr:end]
