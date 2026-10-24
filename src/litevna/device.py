"""LiteVNA register-level access (NanoVNA V2 USB binary protocol; tested on a LiteVNA64, firmware 2.2)."""
from __future__ import annotations

import glob
import struct
import time

import numpy as np


def _find_port() -> str:
    """The first USB CDC serial device (macOS /dev/cu.usbmodem*, Linux /dev/ttyACM*)."""
    ports = sorted(glob.glob('/dev/cu.usbmodem*') + glob.glob('/dev/ttyACM*'))
    if not ports:
        raise RuntimeError('no USB serial VNA found')
    return ports[0]


class LiteVNA:
    """Register-level access: sweep start/step/points/averages, then read the value FIFO."""
    def __init__(self, port: str | None = None):
        import serial
        self.s = serial.Serial(port or _find_port(), 115200, timeout=2)
        self.s.write(bytes(8))  # NOPs resynchronise the protocol parser
        time.sleep(.1)
        self.s.reset_input_buffer()

    def _write(self, addr, fmt, value):
        self.s.write(bytes([{'B': 0x20, 'H': 0x21, 'I': 0x22, 'Q': 0x23}[fmt], addr]) + struct.pack('<' + fmt, value))

    def sweep(self, start_hz: float, stop_hz: float, points: int, averages: int = 1):
        """Frequencies and raw (uncalibrated) S11 and S21 ratios to the forward wave."""
        step = (stop_hz - start_hz) / (points - 1)
        self._write(0x00, 'Q', int(start_hz)); self._write(0x10, 'Q', int(round(step)))
        self._write(0x20, 'H', points); self._write(0x22, 'H', averages)
        self._write(0x30, 'B', 0)  # clear the FIFO, restarting the sweep
        s11, s21 = np.zeros(points, complex), np.zeros(points, complex)
        got = 0
        while got < points * averages:
            n = min(255, points * averages - got)
            self.s.write(bytes([0x18, 0x30, n]))
            data = self.s.read(32 * n)
            if len(data) != 32 * n:
                raise RuntimeError('timeout reading the VNA FIFO')
            for i in range(n):
                f0r, f0i, r0r, r0i, r1r, r1i, idx = struct.unpack_from('<6iH', data, 32 * i)
                fwd = complex(f0r, f0i)
                s11[idx] += complex(r0r, r0i) / fwd; s21[idx] += complex(r1r, r1i) / fwd
            got += n
        return start_hz + step * np.arange(points), s11 / averages, s21 / averages
