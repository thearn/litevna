"""Plots of a folder of captures."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .bands import RACEBAND_HZ


def plot_captures(directory: Path, *, reference: Path | None = None, target_hz: float | None = 5.8e9) -> Path:
    """``s_parameters.png``: S21, S11 and VSWR of every capture in a folder, RaceBand R1 and R8 marked.
    ``reference`` is a CSV of S21 dB columns (frequency_ghz or frequency_hz first) drawn under the S21 panel."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory = Path(directory)
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.7), layout='constrained')
    lo, hi = np.inf, 0.
    if reference:
        ref = np.genfromtxt(reference, delimiter=',', names=True)
        fcol = ref.dtype.names[0]; fr = ref[fcol] * (1e9 if fcol.endswith('_ghz') else 1.)
        for col in ref.dtype.names[1:]:
            ax[0].plot(fr / 1e9, ref[col], lw=1, alpha=.5, label=f'reference {col}')
    for table in sorted(directory.glob('*.csv')):
        d = np.genfromtxt(table, delimiter=',', names=True)
        if 's11_db' not in (d.dtype.names or ()):
            continue
        f = d['frequency_hz'] / 1e9; lo, hi = min(lo, f[0]), max(hi, f[-1])
        line, = ax[1].plot(f, d['s11_db'], lw=2, label=table.stem)
        ax[2].plot(f, d['vswr'], lw=2, color=line.get_color(), label=table.stem)
        if 's21_db' in d.dtype.names:
            ax[0].plot(f, d['s21_db'], lw=2, color=line.get_color(), label=table.stem)
    for a, title in zip(ax, ('S21 (between ports)', 'S11 (port match)', 'VSWR')):
        a.set_title(title, pad=16)
    ax[0].set(ylim=(-40, 0), ylabel='dB'); ax[1].set(ylim=(-40, 0), ylabel='dB'); ax[2].set(ylim=(1, 4))
    for a in ax:
        a.set(xlim=(lo, hi), xlabel='Frequency (GHz)')
        if target_hz:
            a.axvline(target_hz / 1e9, ls='--', c='gray')
        for label, fr in (('R1', RACEBAND_HZ[0]), ('R8', RACEBAND_HZ[-1])):
            a.axvline(fr / 1e9, ls=(0, (2, 2)), c='tab:purple', lw=1.5, alpha=.5)
            a.text(fr / 1e9, 1.01, label, transform=a.get_xaxis_transform(), ha='center', va='bottom',
                   fontsize=10, color='tab:purple')
        a.grid(alpha=.3); a.legend(fontsize=8)
    path = directory / 's_parameters.png'
    fig.savefig(path, dpi=110); plt.close(fig)
    return path
