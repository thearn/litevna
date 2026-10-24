"""Port 1 calibrated by short/open/load (SOL), treated as ideal standards (-1, +1, 0): the one-port error model
e00, e11, de is solved per frequency and inverted. S21 is normalised by a thru sweep (response calibration). Raw
sweeps of each standard live in one ``.npz`` calibration file; a sweep that differs from the stored one discards it."""
from __future__ import annotations

from pathlib import Path

import numpy as np

STANDARDS = ('short', 'open', 'load', 'thru')


def sol_terms(short, open_, load):
    """One-port error terms (e00, e11, de) from raw sweeps of ideal standards; gm = e00 + ga*gm*e11 - ga*de."""
    e00 = np.asarray(load)
    e11 = (open_ + short - 2 * e00) / (open_ - short)
    return e00, e11, short * (1 + e11) - e00


def sol_correct(gm, e00, e11, de):
    """The actual reflection behind a raw reading."""
    return (gm - e00) / (gm * e11 - de)


def save_standard(path: Path, standard: str, f, s11, s21) -> list[str]:
    """Store one standard's raw sweep; returns the standards still missing."""
    path = Path(path)
    cal = dict(np.load(path)) if path.exists() else {}
    if 'frequencies_hz' in cal and not np.array_equal(cal['frequencies_hz'], f):
        cal = {}
    cal['frequencies_hz'] = f
    cal[standard] = s21 if standard == 'thru' else s11
    np.savez(path, **cal)
    return [s for s in STANDARDS if s not in cal]


def calibrate(path: Path, f, s11, s21=None):
    """Calibrated S11 (and S21 when given) of a raw sweep taken at the calibration's frequencies."""
    cal = np.load(path)
    if not np.array_equal(cal['frequencies_hz'], f):
        raise ValueError('sweep differs from the calibration; recalibrate')
    s11 = sol_correct(s11, *sol_terms(cal['short'], cal['open'], cal['load']))
    return s11, (None if s21 is None else s21 / cal['thru'])
