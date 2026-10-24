import csv

import numpy as np
import pytest

import litevna as vna

F = np.linspace(4.8e9, 6.3e9, 31)
E00, E11, DE = 0.1 + 0.05j, 0.2 - 0.1j, 0.3 + 0.2j


def raw(ga):
    return (E00 - DE * ga) / (1 - E11 * ga)


def test_sol_recovers_actual_reflection():
    actual = 0.3 * np.exp(1j * np.linspace(0, 6, F.size))
    terms = vna.sol_terms(raw(-1) + 0 * F, raw(1) + 0 * F, raw(0) + 0 * F)
    assert np.allclose(vna.sol_correct(raw(actual), *terms), actual)


def test_calibration_file_tracks_standards_and_sweep(tmp_path):
    cal = tmp_path / 'cal.npz'
    ones = np.ones(F.size, complex)
    for standard, ga in (('short', -1), ('open', 1), ('load', 0)):
        missing = vna.save_standard(cal, standard, F, raw(ga) * ones, ones)
    assert missing == ['thru']
    assert vna.save_standard(cal, 'thru', F, ones, 0.5 * ones) == []
    s11, s21 = vna.calibrate(cal, F, raw(0.2) * ones, 0.25 * ones)
    assert np.allclose(s11, 0.2) and np.allclose(s21, 0.5)
    with pytest.raises(ValueError):
        vna.calibrate(cal, F[:-1], s11[:-1])
    # a different sweep discards the stored standards
    assert vna.save_standard(cal, 'short', F[:-1], ones[:-1], ones[:-1]) == ['open', 'load', 'thru']


def test_capture_files_round_trip_and_feed_the_overlay(tmp_path):
    s11 = 0.2 * np.exp(1j * np.linspace(0, 3, F.size))
    s21 = np.full(F.size, 0.1 + 0j)
    vna.write_capture(tmp_path, 'port1-rhcp', F, s11, s21)
    f, s = vna.read_touchstone(tmp_path / 'port1-rhcp.s1p')
    assert np.allclose(f, F) and np.allclose(s, s11, atol=1e-6)
    row = next(csv.DictReader(open(tmp_path / 'port1-rhcp.csv')))
    assert float(row['s11_db']) == pytest.approx(-13.979, abs=1e-3)
    assert float(row['vswr']) == pytest.approx(1.5, abs=1e-4)
    assert float(row['s21_db']) == pytest.approx(-20., abs=1e-3)
    assert vna.plot_captures(tmp_path).is_file()


def test_touchstone_db_ghz(tmp_path):
    path = tmp_path / 'a.s1p'
    path.write_text('! comment\n# GHz S DB R 50\n5.8 -20 90\n')
    f, s = vna.read_touchstone(path)
    assert f[0] == 5.8e9 and np.allclose(s, 0.1j)
