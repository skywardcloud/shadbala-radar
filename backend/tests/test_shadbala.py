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
    MEAN_NODE = 7
    TRUE_NODE = 8
    SIDM_LAHIRI = 1

    def set_sid_mode(self, mode, t0=0, ayan_t0=0):
        """Dummy implementation for sidereal mode."""
        self.sid_mode = mode

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


def patch_swe_basic(monkeypatch):
    """Patch swisseph without requiring fastapi for simple unit tests."""
    dummy = DummySwe()

    def julday(y, m, d, h):
        return h / 24.0

    dummy.julday = julday
    sys.modules['swisseph'] = dummy
    import importlib
    shadbala = importlib.import_module('backend.app.shadbala')
    monkeypatch.setattr(shadbala, "swe", dummy)
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


def test_kala_bala_hora_and_friend(monkeypatch):
    """Unequal hora gives full value for lord and partial for friends."""
    shadbala = patch_swe_basic(monkeypatch)
    # 07:30 on a Wednesday -> Moon hora
    ts = datetime(2020, 1, 1, 7, 30, 0)
    res = shadbala.row(ts, 0, 0)
    assert res["Moon"]["kala"] == 60.0

    # 08:30 same day -> Saturn hora, Mercury is friendly to Saturn
    ts2 = datetime(2020, 1, 1, 8, 30, 0)
    res2 = shadbala.row(ts2, 0, 0)
    assert res2["Mercury"]["kala"] == 45.0


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


def test_balas_default_hours(monkeypatch):
    """Ensure hours_ahead path returns correctly shaped data."""
    pytest.importorskip("fastapi")
    patch_swe(monkeypatch)
    from backend.app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/balas", params={"hours_ahead": 1})
    assert resp.status_code == 200
    payload = resp.json()
    assert isinstance(payload["start"], str)
    assert set(payload["data"][0].keys()) == {
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
    }


def test_balas_csv(monkeypatch):
    """CSV endpoint returns downloadable data."""
    pytest.importorskip("fastapi")
    patch_swe(monkeypatch)
    from backend.app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get(
        "/balas.csv",
        params={"start": "2020-01-01T00:00", "end": "2020-01-01T00:10"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment;" in resp.headers.get("content-disposition", "")
    lines = resp.text.strip().splitlines()
    # 3 time points * 7 planets + header
    assert len(lines) == 1 + 3 * 7
    assert lines[0].startswith("timestamp,planet,uccha")
