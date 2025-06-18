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
def get_balas(start: str, end: str, lat: float, lon: float):
    """Temporary /balas route returning submitted parameters.

    This implementation is a placeholder and will be replaced with the
    real logic in a later update.
    """

    return {"start": start, "end": end, "lat": lat, "lon": lon}
