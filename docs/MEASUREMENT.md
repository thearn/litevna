# Measuring built antennas with a VNA

`litevna` drives a LiteVNA (NanoVNA V2 USB binary protocol; tested
on a LiteVNA64, firmware 2.2) to capture calibrated S11 and S21 of a built
antenna, as files an antenna-foundry release overlays on its network plots.

## Commands

```bash
litevna cal short|open|load|thru   # one standard per call
litevna measure DIR NAME [--s21]   # calibrated capture into DIR
litevna plot DIR [--reference CSV] # DIR/s_parameters.png
```

`cal` and `measure` take `--start-ghz 4.8 --stop-ghz 6.3 --points 301 --avg 4`
by default (6.3 GHz is the LiteVNA64's upper limit), `--port` (default: the
first `/dev/cu.usbmodem*` or `/dev/ttyACM*`), and `--cal litevna_cal.npz`. The
calibration file holds the raw sweep of each standard and is only valid for its
own sweep and cables: changing the sweep discards it, and `measure` refuses a
sweep that differs from it. It is not versioned (`*.npz` is ignored).

`measure` prints the best match, the S21 minimum and S11/VSWR at RaceBand R1-R8.

## Calibration

Port 1 is calibrated by short, open and load (SOL) at the end of the cable that
will meet the antenna; the standards are treated as ideal (-1, +1, 0), which is
adequate for |S11| at 5.8 GHz but leaves a small phase error. S21 is normalised
by a thru sweep (response calibration): good for |S21| to about 1 dB at -20 dB,
not for phase.

With the kit's male standards and male-male cables, and an antenna with a
female SMA jack:

1. Port 1, male-male cable, female-female SMA adapter. Run `cal short`, `cal
   open`, `cal load` with each standard on the adapter.
2. Port 2, second male-male cable, joined to the adapter on the port 1 cable.
   Run `cal thru`.
3. Remove the adapter and connect the cables directly to the antenna's jacks.

The calibration plane is the adapter's female face, so removing the adapter
rotates S11 phase by its round-trip length (about 280 degrees at 5.8 GHz for a
20 mm adapter). |S11|, VSWR and the S21 level are essentially unaffected, which
is what the network plots compare. Check after step 1: `measure` with the load
still attached should give |S11| below -30 dB across the band. Do not move the
cables between calibration and measurement.

Keep the antenna away from hands, the desk and metal; nearby objects detune it
and reflect energy from one port into the other.

## Bench practice (the owner's LiteVNA64 and kit)

Learned on the October 2026 sessions (antenna-foundry archive, antenna-foundry archive `examples/VNA_TEST_PLAN_2026-10.md`; the
evidence is in the dated folders it points to).

- **Torque the kit's standards** with an SMA torque wrench, and anything else
  with a hex. A finger-tight short read 1 mm long (168-175 deg instead of 180)
  on a calibration made with seated standards. Antennas with only a knurled nut
  go on finger-tight until they stop.
- **Hold whatever is on port 1 while turning something onto its far end** (an
  adapter, an attenuator), with a second wrench or fingers on its body. Torque
  passed through to the port joint moved an attenuator's input reflection from
  -30 to -8 dB.
- **Check the calibration before each new part of a session, not only after
  calibrating.** The kit's load on port 1 should read below about -40 dB; one
  calibration read -42 dB at 11:00 and -27 dB by early afternoon. Recalibrate
  when it fails. `litevna_cal.npz` holds only the latest calibration: copy it
  into the session folder before recalibrating if the earlier captures may need
  it.
- **Check the port 1 cable's joint at the VNA** before a load check is blamed on the calibration: on 2026-10-12 it was
  found untorqued after a session of swapping standards and adapters (load -10.9 dB, the error's phase turning about
  360 deg per GHz, a reflection some 10 cm behind the plane); torquing it gave -19.4 dB, not the calibration's -41, so
  the joint had settled elsewhere and the calibration was redone.
- **The calibrated plane** with the kit's male standards on the bare port is
  2.6 mm (+- 2) of air inside the port's mating face, measured with a shorted
  stub (antenna-foundry archive, antenna-foundry archive `examples/TBS_Triumph_RHCP/measurements/litevna-2026-10-07`).
- **The VNA reads -40 dB reflections correctly**: a 20 dB attenuator (Amazon
  ASIN B0GHC1T1ZH) with the kit's open, short and load on its far end, solved as
  a two-port, gives a round trip of -40.4 dB. The attenuator's own input match
  (-28 to -33 dB) is poor, so its open or short alone does not read -40 dB flat.
- **Lying on the table or held makes no difference** (antenna out past the
  table's edge, white non-metal table): table against air differed by -32 to
  -38 dB, no more than repeating either. Not tested with the antenna over the
  table.
- **Typical refit spread** (unscrew, refit, capture again): vector difference
  -26 to -34 dB. A change smaller than that is handling.
- **RP-SMA.** A knurled nut with a centre socket is RP-SMA male: it screws onto
  port 1 but makes no centre contact and reads as an open (0 dB, 0 deg) at the
  port. Check for a pin before capturing. No RP-SMA short/open/load kit was
  found for sale (RP-SMA male loads exist), so RP antennas are measured through
  an adapter chain after the calibration plane: its length only turns the phase,
  but its reflection stays in, so depths are less reliable than frequencies and
  band edges.
- **Characterise an adapter chain** by capturing it open on the calibrated port
  and fitting a straight line to the unwrapped phase; the one-way delay as mm of
  air is its electrical length. The owner's chains (2026-10-08,
  antenna-foundry archive `examples/Goggle_Stock_Linear_Dipole/measurements/litevna-2026-10-08`):

  | chain on port 1 | one-way delay, mm of air |
  |---|---|
  | SMA male-male (hex) + SMA female / RP-SMA female (knurled) | 35.0 |
  | the same male-male + plain SMA female-female | 34.0 |

- **An adapter moves the antenna, not just the phase,** when the antenna has no
  balun: a stock dipole's upper band edge fell about 200 MHz on 34 mm of
  adapters. Compare antennas only on the same mount, and model the mount.

## Files

Captures of an example's physical unit go in
`examples/<example>/measurements/<instrument>-<date>/`, tracked in Git
(`outputs/` is regenerated by publication and ignored). Each capture `NAME`:

- `NAME.s1p`: calibrated complex S11 at the port 1 connector (Touchstone, RI).
- `NAME.csv`: `frequency_hz, s11_db, vswr` and, with `--s21`, `s21_db`.

Name a capture after what port 1 is on (`port1-rhcp`, `port1-lhcp`). Add a
README with the unit, instrument, sweep, calibration and anything unusual, and
`vna plot` for a quick look (RaceBand R1 and R8 marked; `--reference` draws a
reference S21 CSV under the S21 panel).

## Comparison with the model

List a capture in the example's `measured` entries in
`validation/publish_examples.py`: one `MeasuredSpec` per trace, with the CSV
column as its unit column and the model port ids as `receive`/`excite`, for
example

```python
MeasuredSpec(label='GEPRC unit S11 RHCP (LiteVNA)', file=f'{TFP1_LITEVNA}/port1-rhcp.csv',
             receive='RHCP', excite='RHCP', frequency_column='frequency_hz',
             unit_columns=('s11_db',), color='tab:purple')
```

Publication then overlays it on every tier's `s-parameters.png` (|S| in dB, and
VSWR for reflection traces) next to the reference measurements.
