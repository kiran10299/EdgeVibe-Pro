import numpy as np
import threading

class RingBuffer:
    """Thread-safe circular ring buffer for zero-copy high-throughput sensor streaming."""

    def __init__(self, capacity: int, channels: int = 1):
        self.capacity = capacity
        self.channels = channels
        self.buffer = np.zeros((capacity, channels), dtype=np.float32)
        self.write_idx = 0
        self.size = 0
        self.lock = threading.Lock()

    def write(self, data: np.ndarray) -> None:
        """Appends a 2D chunk of shape (N, channels) into circular buffer."""
        data = np.asarray(data, dtype=np.float32)
        n = data.shape[0]
        if n == 0:
            return

        with self.lock:
            if n >= self.capacity:
                # Chunk larger than buffer: keep only most recent capacity samples
                self.buffer[:] = data[-self.capacity:]
                self.write_idx = 0
                self.size = self.capacity
            else:
                end = self.write_idx + n
                if end <= self.capacity:
                    self.buffer[self.write_idx:end] = data
                else:
                    first_part = self.capacity - self.write_idx
                    self.buffer[self.write_idx:] = data[:first_part]
                    self.buffer[:end - self.capacity] = data[first_part:]
                self.write_idx = (self.write_idx + n) % self.capacity
                self.size = min(self.capacity, self.size + n)

    def get_latest(self, num_samples: int) -> np.ndarray:
        """Retrieves the most recent `num_samples` without advancing read pointer."""
        with self.lock:
            n = min(num_samples, self.size)
            if n == 0:
                return np.zeros((0, self.channels), dtype=np.float32)

            start = (self.write_idx - n) % self.capacity
            if start + n <= self.capacity:
                return self.buffer[start:start + n].copy()
            else:
                part1 = self.buffer[start:].copy()
                part2 = self.buffer[:(start + n) % self.capacity].copy()
                return np.vstack((part1, part2))

    def clear(self) -> None:
        with self.lock:
            self.write_idx = 0
            self.size = 0
            self.buffer.fill(0)
