import sys
import importlib
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class DummySwe:
    SUN = 0
    MOON = 1
    MARS = 2
    MERCURY = 3
    JUPITER = 4
    VENUS = 5
    SATURN = 6
    SIDM_LAHIRI = 1

    def set_sid_mode(self, mode, t0=0, ayan_t0=0):
        pass

    def julday(self, y, m, d, h):
        return 0.0

    def calc_ut(self, jd, pid):
        return (0, 0, 0, 0)


def load_module():
    dummy = DummySwe()
    sys.modules["swisseph"] = dummy
    shadbala = importlib.import_module("backend.app.shadbala")
    shadbala.swe = dummy
    return shadbala


def test_drik_bala_signed_average():
    shadbala = load_module()
    positions = {
        "Sun": 0.0,
        "Moon": 0.0,
        "Mars": 0.0,
        "Mercury": 0.0,
        "Jupiter": 0.0,
        "Venus": 0.0,
        "Saturn": 0.0,
    }
    result = shadbala._drik_bala(0.0, "Sun", positions)
    assert result == pytest.approx(120.0)


def test_drik_bala_no_others():
    shadbala = load_module()
    assert shadbala._drik_bala(0.0, "Sun", {"Sun": 0.0}) == 0.0
