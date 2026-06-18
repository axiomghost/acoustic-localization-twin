"""Tests for SimplePropagation model."""
import numpy as np
import pytest
from engine.propagation import SimplePropagation, SPEED_OF_SOUND


def test_toa_zero_distance():
    """Source at sensor position => TOA = 0."""
    prop = SimplePropagation()
    pos = np.array([10.0, 20.0])
    assert prop.compute_toa(pos, pos) == pytest.approx(0.0)


def test_toa_known_distance():
    """343 m at 343 m/s => 1.0 s."""
    prop = SimplePropagation()
    src = np.array([0.0, 0.0])
    sensor = np.array([343.0, 0.0])
    assert prop.compute_toa(src, sensor) == pytest.approx(1.0, rel=1e-9)


def test_toa_custom_speed():
    prop = SimplePropagation(speed=300.0)
    src = np.array([0.0, 0.0])
    sensor = np.array([150.0, 0.0])
    assert prop.compute_toa(src, sensor) == pytest.approx(0.5, rel=1e-9)


def test_toa_symmetry():
    """TOA must be symmetric: source->sensor == sensor->source."""
    prop = SimplePropagation()
    a = np.array([10.0, 30.0])
    b = np.array([80.0, 120.0])
    assert prop.compute_toa(a, b) == pytest.approx(prop.compute_toa(b, a))


def test_toa_pythagorean():
    """3-4-5 triangle at 343 m/s => TOA = 5/343."""
    prop = SimplePropagation()
    src = np.array([0.0, 0.0])
    sensor = np.array([3.0, 4.0])   # distance = 5 m
    assert prop.compute_toa(src, sensor) == pytest.approx(5.0 / SPEED_OF_SOUND, rel=1e-9)
