from fastapi import FastAPI
from datetime import datetime, timedelta
from .shadbala import row

app = FastAPI()

@app.get("/balas")
def balas(hours_ahead: int = 24,
          lat: float = 40.7128,
          lon: float = -74.0060):
    now = datetime.utcnow()
    frames = [row(now + timedelta(minutes=5*i), lat, lon)
              for i in range(int(hours_ahead*12))]
    return {"start": now, "interval": "5m", "data": frames}
