import numpy as np

from litevna import compare

F = np.linspace(4.8e9, 6.3e9, 301)


def notch(f0, depth=0.05):
    x = (F - f0) / 0.3e9
    return depth + (1 - depth) * x ** 2 / (1 + x ** 2) + 0j


def test_summary_finds_minimum_and_shift():
    model, meas = notch(5.8e9), notch(5.75e9)
    s = compare.summary(F, model, (F, meas))
    assert abs(s['min_hz'] - 5.8e9) < 10e6
    assert abs(s['d_min_hz'] - 50e6) < 10e6
    assert s['rmse_db'] > 0


def test_residual_is_zero_on_itself():
    g = notch(5.8e9)
    r = compare.residual((F, g))
    assert np.allclose(r(F, g), 0)
