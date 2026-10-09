import pytest
import numpy as np
from edge_vibe.daq.ring_buffer import RingBuffer

def test_ring_buffer_basic():
    rb = RingBuffer(capacity=100, channels=2)
    assert rb.size == 0

    chunk = np.ones((40, 2))
    rb.write(chunk)
    assert rb.size == 40

    latest = rb.get_latest(20)
    assert latest.shape == (20, 2)
    assert np.all(latest == 1.0)

def test_ring_buffer_overflow_wrap():
    rb = RingBuffer(capacity=50, channels=1)
    chunk1 = np.full((40, 1), 5.0)
    chunk2 = np.full((30, 1), 10.0)

    rb.write(chunk1)
    rb.write(chunk2)

    assert rb.size == 50
    latest = rb.get_latest(30)
    assert np.all(latest == 10.0)
