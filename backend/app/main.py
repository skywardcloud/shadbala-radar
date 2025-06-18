from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

try:
    # When executed as part of the package
    from .shadbala import row
except ImportError:  # pragma: no cover - allow running file directly
    # Fallback for running `python main.py` during development
    from shadbala import row

app = FastAPI()

@app.get("/balas")
def balas(hours_ahead: int | None = 24,
          start: str | None = None,
          end: str | None = None,
          lat: float = 40.7128,
          lon: float = -74.0060):
    """Return shadbala rows every 5 minutes.

    Either ``hours_ahead`` or both ``start`` and ``end`` can be supplied. When
    ``start``/``end`` are provided they are interpreted as datetimes in the
    ``America/New_York`` timezone and the range may not exceed 24 hours.
    """

    tz = ZoneInfo("America/New_York")

    if start and end:
        start_dt = datetime.fromisoformat(start).replace(tzinfo=tz)
        end_dt = datetime.fromisoformat(end).replace(tzinfo=tz)
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
    frames = [row(now + timedelta(minutes=5*i), lat, lon)
              for i in range(int(hours_ahead * 12))]
    return {"start": now, "interval": "5m", "data": frames}
