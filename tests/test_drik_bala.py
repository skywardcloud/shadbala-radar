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
        "Moon": 180.0,
        "Mars": 90.0,
        "Mercury": 180.0,
        "Jupiter": 120.0,
        "Venus": 180.0,
        "Saturn": 60.0,
    }
    result = shadbala._drik_bala(0.0, "Sun", positions)
    # With aspects measured from the aspecting planet to the target,
    # benefics contribute positively while malefics reduce the score.
    # The configuration below should yield a total of 96.
    assert result == pytest.approx(96.0)


def test_drik_bala_no_others():
    shadbala = load_module()
    assert shadbala._drik_bala(0.0, "Sun", {"Sun": 0.0}) == 0.0
