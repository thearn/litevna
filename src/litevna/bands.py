"""Channel plans and small reflection helpers shared by the package."""
from __future__ import annotations

import numpy as np

RACEBAND_HZ = (5658e6, 5695e6, 5732e6, 5769e6, 5806e6, 5843e6, 5880e6, 5917e6)   # R1-R8


def vswr(g):
    a = np.minimum(abs(np.asarray(g)), .999999)
    return (1 + a) / (1 - a)
