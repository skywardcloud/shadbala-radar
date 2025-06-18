import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from datetime import datetime


class DummySwe:
    SUN = 0
    MOON = 1
    MARS = 2
    MERCURY = 3
    JUPITER = 4
    VENUS = 5
    SATURN = 6

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
        }
        return longs[pid]

def patch_swe(monkeypatch):
    dummy = DummySwe()
    sys.modules['swisseph'] = dummy
    import importlib
    shadbala = importlib.import_module('backend.app.shadbala')
    monkeypatch.setattr(shadbala, "swe", dummy)
    try:
        pytest.importorskip("fastapi")
        main = importlib.import_module('backend.app.main')
        monkeypatch.setattr(main, "row", shadbala.row)
    except ModuleNotFoundError:
        pass
    return shadbala


def test_row_structure(monkeypatch):
    shadbala = patch_swe(monkeypatch)
    ts = datetime(2020, 1, 1, 12, 0, 0)
    res = shadbala.row(ts, 0, 0)
    planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
    assert set(res.keys()) == planets
    for val in res.values():
        assert set(val.keys()) == {"uccha", "dig", "kala", "cheshta", "naisargika", "drik"}


def test_row_values(monkeypatch):
    shadbala = patch_swe(monkeypatch)
    ts = datetime(2020, 1, 1, 12, 0, 0)
    res = shadbala.row(ts, 0, 0)
    assert abs(res["Sun"]["uccha"] - 60.0) < 1e-6
    assert abs(res["Moon"]["dig"] - 40.0) < 1e-6
    assert abs(res["Venus"]["cheshta"] - 50.0) < 1e-6
    assert abs(res["Jupiter"]["kala"] - 30.0) < 1e-6


def test_balas_endpoint(monkeypatch):
    pytest.importorskip("fastapi")
    shadbala = patch_swe(monkeypatch)
    from backend.app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/balas",
        params={"start": "2020-01-01T00:00", "end": "2020-01-01T01:00"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["data"]) == 13
    assert set(payload["data"][0].keys()) == {
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
    }
