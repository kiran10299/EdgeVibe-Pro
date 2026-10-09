import sqlite3
import datetime
from typing import Dict, Any

class TimeSeriesLogger:
    """Logs extracted DSP features and alarms to an indexed SQLite database."""

    def __init__(self, db_path: str = "edgevibe_telemetry.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    vibe_rms REAL,
                    vibe_peak REAL,
                    kurtosis REAL,
                    crest_factor REAL,
                    peak_freq_hz REAL,
                    temp_c REAL,
                    force_n REAL,
                    iso_zone TEXT,
                    is_trip INTEGER
                )
            """)
            conn.commit()

    def log_record(
        self,
        features: Dict[str, Any],
        peak_freq: float,
        temp_c: float,
        force_n: float,
        iso_zone: str,
        is_trip: bool
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO telemetry (timestamp, vibe_rms, vibe_peak, kurtosis, crest_factor, peak_freq_hz, temp_c, force_n, iso_zone, is_trip)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now,
                features.get("rms", 0.0),
                features.get("peak", 0.0),
                features.get("kurtosis", 3.0),
                features.get("crest_factor", 1.0),
                peak_freq,
                temp_c,
                force_n,
                iso_zone,
                1 if is_trip else 0
            ))
            conn.commit()
