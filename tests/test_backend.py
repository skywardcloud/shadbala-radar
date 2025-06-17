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
    assert "sun_long" in result
    assert isinstance(result["sun_long"], float)


def test_balas_endpoint_time_series_length():
    client = TestClient(app)
    hours = 1
    resp = client.get("/balas", params={"hours_ahead": hours})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["interval"] == "5m"
    assert len(payload["data"]) == hours * 12
    assert isinstance(payload["data"][0], dict)
    assert "sun_long" in payload["data"][0]
