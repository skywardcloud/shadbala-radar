from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

try:
    # When executed as part of the package
    from .shadbala import row
except ImportError:  # pragma: no cover - allow running file directly
    # Fallback for running `python main.py` during development
    from shadbala import row

app = FastAPI()

origins_env = os.getenv("ALLOWED_ORIGINS")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://fantastic-space-cod-5g57gw9764p9374gr-5173.app.github.dev",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/balas")
def get_balas(
    start: str | None = None,
    end: str | None = None,
    hours_ahead: int | None = None,
    lat: float = 0.0,
    lon: float = 0.0,
):
    """Return Shadbala values sampled every five minutes."""

    if hours_ahead is not None and (start or end):
        raise HTTPException(status_code=400, detail="Provide either hours_ahead or start/end")

    tz = ZoneInfo("America/New_York")

    if hours_ahead is not None:
        start_dt = datetime.now(tz)
        end_dt = start_dt + timedelta(hours=hours_ahead)
    else:
        if not start or not end:
            raise HTTPException(status_code=400, detail="start and end required")
        try:
            start_dt = datetime.fromisoformat(start).replace(tzinfo=tz)
            end_dt = datetime.fromisoformat(end).replace(tzinfo=tz)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format")

    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="end must be after start")

    if end_dt - start_dt > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Range may not exceed 24 hours")

    current = start_dt
    rows = []
    while current <= end_dt:
        rows.append(row(current, lat=lat, lon=lon))
        current += timedelta(minutes=5)

    return {
        "start": start_dt.isoformat(timespec="minutes"),
        "end": end_dt.isoformat(timespec="minutes"),
        "interval": "5m",
        "data": rows,
    }
