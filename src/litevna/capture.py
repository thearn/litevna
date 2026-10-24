"""Captures: ``<name>.s1p`` (calibrated complex S11 at the port 1 connector, Touchstone RI) and ``<name>.csv``
(frequency_hz, s11_db, vswr, and s21_db when measured), and reading Touchstone one-ports back."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .bands import RACEBAND_HZ, vswr


def read_touchstone(path: Path):
    """Frequencies (Hz) and complex S11 of a one-port Touchstone file (RI, MA or DB; Hz to GHz)."""
    unit, fmt, rows = 1e9, 'MA', []  # Touchstone defaults: GHz, MA
    for line in Path(path).read_text().splitlines():
        line = line.split('!')[0].strip()
        if line.startswith('#'):
            opts = line[1:].upper().split()
            unit = next((dict(HZ=1., KHZ=1e3, MHZ=1e6, GHZ=1e9)[o] for o in opts if o.endswith('HZ')), 1e9)
            fmt = next((o for o in opts if o in ('RI', 'MA', 'DB')), 'MA')
        elif line:
            rows.append([float(v) for v in line.split()[:3]])
    d = np.array(rows)
    a, b = d[:, 1], d[:, 2]
    s = a + 1j * b if fmt == 'RI' else (a if fmt == 'MA' else 10 ** (a / 20)) * np.exp(1j * np.radians(b))
    return d[:, 0] * unit, s


def write_capture(directory: Path, name: str, f, s11, s21=None) -> list[Path]:
    """``<name>.s1p`` (Touchstone, RI) and ``<name>.csv`` (frequency_hz, s11_db, vswr[, s21_db])."""
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    s1p, table = directory / f'{name}.s1p', directory / f'{name}.csv'
    with open(s1p, 'w') as out:
        out.write('! LiteVNA S11, SOL calibrated at the port 1 connector\n# Hz S RI R 50\n')
        for fr, g in zip(f, s11):
            out.write(f'{fr:.0f} {g.real:.6e} {g.imag:.6e}\n')
    with open(table, 'w', newline='') as out:
        w = csv.writer(out)
        w.writerow(['frequency_hz', 's11_db', 'vswr'] + (['s21_db'] if s21 is not None else []))
        for i, fr in enumerate(f):
            row = [f'{fr:.0f}', f'{20 * np.log10(abs(s11[i])):.3f}', f'{vswr(s11[i]):.4f}']
            w.writerow(row + ([f'{20 * np.log10(abs(s21[i])):.3f}'] if s21 is not None else []))
    return [s1p, table]


def summary(f, s11, s21=None) -> list[str]:
    """Printable lines: best match, S21 minimum, and S11/VSWR at RaceBand R1-R8."""
    rl = -20 * np.log10(abs(s11)); i = int(np.argmax(rl))
    lines = [f'best match {f[i] / 1e6:.1f} MHz: S11 {-rl[i]:.1f} dB, VSWR {vswr(s11[i]):.2f}']
    if s21 is not None:
        db = 20 * np.log10(abs(s21)); k = int(np.argmin(db))
        lines.append(f'S21 minimum {db[k]:.1f} dB at {f[k] / 1e6:.1f} MHz')
    for n, fr in enumerate(RACEBAND_HZ, 1):
        if f[0] <= fr <= f[-1]:
            j = int(np.argmin(abs(f - fr)))
            lines.append(f'  R{n} {f[j] / 1e6:7.1f} MHz  S11 {-rl[j]:6.1f} dB  VSWR {vswr(s11[j]):.2f}')
    return lines
