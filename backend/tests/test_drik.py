import sys
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

class DummySwe:
    SUN = 0
    MOON = 1
    MARS = 2
    MERCURY = 3
    JUPITER = 4
    VENUS = 5
    SATURN = 6
    MEAN_NODE = 7
    TRUE_NODE = 8
    SIDM_LAHIRI = 1
    def set_sid_mode(self, mode, t0=0, ayan_t0=0):
        pass
    def julday(self, y,m,d,h):
        return 0.0
    def calc_ut(self, jd, pid):
        return (0,0,0,0)

def load_module():
    dummy = DummySwe()
    sys.modules['swisseph'] = dummy
    shadbala = importlib.import_module('backend.app.shadbala')
    shadbala.swe = dummy
    return shadbala

def test_drik_bala_negative():
    shadbala = load_module()
    positions = {"Sun": 10, "Mars": 10}
    result = shadbala._drik_bala(10, "Sun", positions)
    assert result == -60.0
