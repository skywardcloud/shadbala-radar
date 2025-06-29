from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import csv
from io import StringIO

try:
    # When executed as part of the package
    from .shadbala import row
except ImportError:  # pragma: no cover - allow running file directly
    # Fallback for running `python main.py` during development
    from shadbala import row

app = FastAPI(root_path=os.getenv("ROOT_PATH", ""))

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

origins_env = os.getenv("ALLOWED_ORIGINS")
if origins_env:
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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

    hours_ahead: int | None = 24,
    start: str | None = None,
    end: str | None = None,
    lat: float = 40.7128,
    lon: float = -74.0060,
    use_true_node: bool = False,
):
    """Return shadbala rows every 5 minutes.

    Either ``hours_ahead`` or both ``start`` and ``end`` can be supplied. When
    ``start``/``end`` are provided they are parsed as ISO 8601 datetimes. If no
    timezone is included they are assumed to be in the ``America/New_York``
    timezone. The range may not exceed 24 hours.
    """

    start_utc, frames = _collect_data(hours_ahead, start, end, lat, lon, use_true_node)
    return {"start": start_utc.isoformat(), "interval": "5m", "data": frames}


def _collect_data(
    hours_ahead: int | None,
    start: str | None,
    end: str | None,
    lat: float,
    lon: float,
    use_true_node: bool,
):
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
            frames.append(row(current, lat, lon, use_true_node=use_true_node))
            current += timedelta(minutes=5)
        return start_utc, frames

    now = datetime.utcnow()
    if hours_ahead is None:
        hours_ahead = 24
    frames = [
        row(now + timedelta(minutes=5 * i), lat, lon, use_true_node=use_true_node)
        for i in range(int(hours_ahead * 12))
    ]
    return now, frames


@app.get("/balas.csv")
def get_balas_csv(
    hours_ahead: int | None = 24,
    start: str | None = None,
    end: str | None = None,
    lat: float = 40.7128,
    lon: float = -74.0060,
    use_true_node: bool = False,
):
    """Return shadbala rows as CSV."""

    start_utc, frames = _collect_data(hours_ahead, start, end, lat, lon, use_true_node)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "planet", "uccha", "dig", "kala", "cheshta", "naisargika", "drik"])

    for i, frame in enumerate(frames):
        ts = start_utc + timedelta(minutes=5 * i)
        for planet, metrics in frame.items():
            writer.writerow([
                ts.isoformat(),
                planet,
                metrics["uccha"],
                metrics["dig"],
                metrics["kala"],
                metrics["cheshta"],
                metrics["naisargika"],
                metrics["drik"],
            ])

    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=balas.csv"},
    )

