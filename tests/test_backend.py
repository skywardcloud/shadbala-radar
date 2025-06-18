import pytest
from datetime import datetime

pytest.importorskip("swisseph")
pytest.importorskip("fastapi")

from backend.app.shadbala import row
from backend.app.main import app
from fastapi.testclient import TestClient


def test_row_returns_expected_structure():
    result = row(datetime.utcnow(), lat=40.0, lon=0.0)
    assert isinstance(result, dict)
    assert "Sun" in result
    assert set(result["Sun"].keys()) == {"uccha", "dig", "kala", "cheshta", "naisargika", "drik"}


def test_balas_endpoint_time_series_length():
    client = TestClient(app)
    start = "2020-01-01T00:00"
    end = "2020-01-01T01:00"
    resp = client.get("/balas", params={"start": start, "end": end})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["interval"] == "5m"
    assert len(payload["data"]) == 12 + 1  # inclusive of start and end
    assert isinstance(payload["data"][0], dict)
    assert "Sun" in payload["data"][0]


def test_allowed_origins_env(monkeypatch):
    import importlib
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com")
    import backend.app.main as main
    importlib.reload(main)
    assert "https://example.com" in main.app.user_middleware[0].options["allow_origins"]

