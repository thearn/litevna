"""A model's reflection against a VNA capture: the match's summary figures and the fit residual (used to score
a model against a measured unit when fitting it).

``summary``: the minimum (frequency, dB, VSWR), the VSWR 2 band's edges and the VSWR at given channels; against a
reference trace also the |S11| RMSE over ``db_band``, the complex RMS difference over ``fit_band`` and the minimum's
shift. ``residual``: [re, im] of model minus capture on a grid over ``fit_band``, then the |S11| dB difference over
``db_band`` times ``db_weight`` (1 dB weighs as 1.0 of complex reflection at the default)."""
from __future__ import annotations

import numpy as np

from .bands import vswr

RACEBAND = {'R1': 5658e6, 'R4': 5769e6, 'R8': 5917e6}


def _on(grid, f, g):
    return np.interp(grid, f, g.real) + 1j * np.interp(grid, f, g.imag)


def summary(f, g, ref=None, *, band=(4.8e9, 6.3e9), db_band=(5.3e9, 6.1e9), fit_band=None, channels=RACEBAND) -> dict:
    f = np.asarray(f); g = np.asarray(g)
    db = 20 * np.log10(np.maximum(abs(g), 1e-9)); v = vswr(g)
    inside = (f >= band[0]) & (f <= band[1])
    i = int(np.argmin(np.where(inside, db, np.inf)))
    out = {'min_hz': float(f[i]), 'min_db': round(float(db[i]), 2), 'min_vswr': round(float(v[i]), 3)}
    under = np.where(inside & (v < 2))[0]
    if len(under):
        lo, hi = under[0], under[-1]
        edge = lambda a, b: float(f[a] + (f[b] - f[a]) * (2 - v[a]) / (v[b] - v[a])) if v[a] != v[b] else float(f[a])
        out['vswr2_lo_hz'] = edge(lo - 1, lo) if lo > 0 and inside[lo - 1] else None
        out['vswr2_hi_hz'] = edge(hi, hi + 1) if hi + 1 < len(f) and inside[hi + 1] else None
    out.update({k: round(float(np.interp(fk, f, v)), 3) for k, fk in channels.items()})
    if ref is not None:
        fr, gr = (np.asarray(x) for x in ref)
        gm = _on(fr, f, g)
        sel = (fr >= db_band[0]) & (fr <= db_band[1])
        out['rmse_db'] = round(float(np.sqrt(np.mean((20 * np.log10(abs(gm[sel])) - 20 * np.log10(abs(gr[sel]))) ** 2))), 3)
        whole = (fr >= (fit_band or band)[0]) & (fr <= (fit_band or band)[1])
        out['complex_rms'] = round(float(np.sqrt(np.mean(abs(gm[whole] - gr[whole]) ** 2))), 4)
        out['d_min_hz'] = out['min_hz'] - summary(fr, gr, band=band, channels={})['min_hz']
    return out


def residual(ref, *, fit_band=(4.8e9, 6.3e9), db_band=(5.3e9, 6.1e9), step_hz=25e6, db_weight=1.):
    """A function of a model trace (f, g) returning the fit's residual vector against the capture ``ref`` (f, g)."""
    fr, gr = (np.asarray(x) for x in ref)
    grid = np.arange(fit_band[0], fit_band[1] + 1, step_hz)
    gref = _on(grid, fr, gr)
    sel = (grid >= db_band[0]) & (grid <= db_band[1])

    def r(f, g):
        gm = _on(grid, np.asarray(f), np.asarray(g))
        d = gm - gref
        return np.r_[d.real, d.imag, db_weight * (20 * np.log10(abs(gm[sel])) - 20 * np.log10(abs(gref[sel])))]
    return r
