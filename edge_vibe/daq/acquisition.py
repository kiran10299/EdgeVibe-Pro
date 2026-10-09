import threading
import time
import numpy as np
from typing import Optional
from edge_vibe.daq.ring_buffer import RingBuffer
from edge_vibe.daq.sim_channels import IndustrialSignalGenerator

class DaqWorker:
    """High-speed asynchronous sensor ingestion worker thread."""

    def __init__(self, sample_rate_hz: int = 1000, buffer_capacity: int = 10000):
        self.fs = sample_rate_hz
        self.channels = 4
        self.ring_buffer = RingBuffer(capacity=buffer_capacity, channels=self.channels)
        self.signal_gen = IndustrialSignalGenerator(sample_rate_hz=sample_rate_hz)
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        # Stream in 50ms blocks (e.g. 50 samples per block at 1000 Hz)
        block_size = int(self.fs * 0.05)
        dt_block = 0.05

        while self.running:
            t_start = time.time()
            data_block = self.signal_gen.generate_chunk(block_size)
            self.ring_buffer.write(data_block)
            elapsed = time.time() - t_start
            sleep_time = max(0.001, dt_block - elapsed)
            time.sleep(sleep_time)

    def set_fault_severity(self, factor: float) -> None:
        self.signal_gen.set_fault_severity(factor)
