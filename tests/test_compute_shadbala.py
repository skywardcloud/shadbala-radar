import sys
import importlib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

    def julday(self, y, m, d, h):
        return 0.0

    def calc_ut(self, jd, pid):
        longs = {
            0: (10, 0, 1, 1),
            1: (40, 0, 1, 1),
            2: (70, 0, 1, 1),
            3: (100, 0, 1, 1),
            4: (130, 0, 1, 1),
            5: (160, 0, 1, 1),
            6: (190, 0, 1, 1),
            7: (220, 0, 1, 1),
            8: (40, 0, 1, 1),
        }
        return longs[pid]


def load_module(monkeypatch):
    dummy = DummySwe()
    sys.modules["swisseph"] = dummy
    shadbala = importlib.import_module("backend.app.shadbala")
    monkeypatch.setattr(shadbala, "swe", dummy)
    return shadbala


def test_compute_shadbala_structure(monkeypatch):
    shadbala = load_module(monkeypatch)
    ts = datetime(2020, 1, 1, 12, 0, 0)
    res = shadbala.compute_shadbala(ts, 0, 0)
    planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    assert set(res.keys()) == planets
    for metrics in res.values():
        assert set(metrics.keys()) == {
            "sth\u0101na",
            "dig",
            "k\u0101la",
            "cheshta",
            "naisargika",
            "drik",
            "total",
        }
