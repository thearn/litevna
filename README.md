# litevna

Capture calibrated S11 and S21 from a LiteVNA (NanoVNA V2 USB binary protocol)
and compare a model's reflection with a measured unit.

Split out of antenna-foundry on 2026-10-24 (old `vna.py` and
`network/capture.py` at revision `82b4d30`). It has no antenna-foundry
dependency; the foundry imports it to read captures.

```bash
pip install -e '.[test]'
litevna cal short|open|load|thru      # one standard per call
litevna measure DIR NAME [--s21]      # calibrated capture into DIR
litevna plot DIR [--reference CSV]    # DIR/s_parameters.png
```

| Module | What it does |
|---|---|
| `device` | register-level sweep over USB serial |
| `cal` | SOL one-port and thru response calibration, the `.npz` calibration file |
| `capture` | `.s1p`/`.csv` captures, Touchstone reading, printed summary at RaceBand |
| `compare` | model-against-capture summary figures and fit residual |
| `plot` | S21/S11/VSWR of a folder of captures |

Calibration practice and bench lessons are in `docs/MEASUREMENT.md`.
