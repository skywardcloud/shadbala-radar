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
        "https://fantastic-space-cod-5g57gw9764p9374gr-5173.app.github.dev"
    ]

codespace = os.getenv("CODESPACE_NAME")
if codespace:
    allowed_origins.append(f"https://5173-{codespace}.app.github.dev")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/balas")
def get_balas(

    hours_ahead: int | None = 24,
    start: str | None = None,
    end: str | None = None,
    lat: float = 40.7128,
    lon: float = -74.0060,
):
    """Return shadbala rows every 5 minutes.

    Either ``hours_ahead`` or both ``start`` and ``end`` can be supplied. When
    ``start``/``end`` are provided they are parsed as ISO 8601 datetimes. If no
    timezone is included they are assumed to be in the ``America/New_York``
    timezone. The range may not exceed 24 hours.
    """

    tz = ZoneInfo("America/New_York")

    if start and end:
        start_dt = datetime.fromisoformat(start)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=tz)
        else:
            start_dt = start_dt.astimezone(tz)

        end_dt = datetime.fromisoformat(end)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=tz)
        else:
            end_dt = end_dt.astimezone(tz)
        start_utc = start_dt.astimezone(ZoneInfo("UTC"))
        end_utc = end_dt.astimezone(ZoneInfo("UTC"))

        if end_utc <= start_utc:
            raise HTTPException(status_code=400, detail="end must be after start")
        if end_utc - start_utc > timedelta(hours=24):
            raise HTTPException(status_code=400, detail="range cannot exceed 24 hours")

        frames = []
        current = start_utc
        while current <= end_utc:
            frames.append(row(current, lat, lon))
            current += timedelta(minutes=5)
        return {"start": start_utc.isoformat(), "interval": "5m", "data": frames}

    now = datetime.utcnow()
    if hours_ahead is None:
        hours_ahead = 24
    frames = [row(now + timedelta(minutes=5 * i), lat, lon) for i in range(int(hours_ahead * 12))]
    return {"start": now.isoformat(), "interval": "5m", "data": frames}

