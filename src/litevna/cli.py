"""``litevna cal|measure|plot``: see docs/MEASUREMENT.md."""
from __future__ import annotations

import argparse
from pathlib import Path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog='litevna', description='Calibrate a LiteVNA and capture S11/S21 of a built antenna')
    sub = p.add_subparsers(dest='command', required=True)
    for name in ('cal', 'measure'):
        q = sub.add_parser(name)
        if name == 'cal':
            q.add_argument('standard', choices=('short', 'open', 'load', 'thru'))
        else:
            q.add_argument('directory', type=Path); q.add_argument('name')
            q.add_argument('--s21', action='store_true', help='also record S21 (port 2 on the other jack)')
        q.add_argument('--port', help='serial device (default: the first USB modem)')
        q.add_argument('--start-ghz', type=float, default=4.8); q.add_argument('--stop-ghz', type=float, default=6.3)
        q.add_argument('--points', type=int, default=301); q.add_argument('--avg', type=int, default=4)
        q.add_argument('--cal', type=Path, default=Path('litevna_cal.npz'), help='calibration file')
    q = sub.add_parser('plot'); q.add_argument('directory', type=Path)
    q.add_argument('--reference', type=Path, help='CSV of reference S21 (dB) columns to draw under the S21 panel')
    args = p.parse_args(argv)

    import litevna as vna
    if args.command == 'plot':
        print(vna.plot_captures(args.directory, reference=args.reference)); return 0
    f, s11, s21 = vna.LiteVNA(args.port).sweep(args.start_ghz * 1e9, args.stop_ghz * 1e9, args.points, args.avg)
    if args.command == 'cal':
        missing = vna.save_standard(args.cal, args.standard, f, s11, s21)
        print(f'saved {args.standard}; still needed: {", ".join(missing) or "none"}'); return 0
    s11, s21 = vna.calibrate(args.cal, f, s11, s21 if args.s21 else None)
    for path in vna.write_capture(args.directory, args.name, f, s11, s21):
        print(path)
    print('\n'.join(vna.summary(f, s11, s21))); return 0


if __name__ == '__main__':
    raise SystemExit(main())
