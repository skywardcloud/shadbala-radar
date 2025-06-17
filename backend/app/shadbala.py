from datetime import datetime, timedelta
import swisseph as swe

def row(timestamp: datetime, lat: float, lon: float):
    """Return dict of {planet: {uccha: …, dig: …, …}} for one instant."""
    jd = swe.julday(timestamp.year, timestamp.month, timestamp.day,
                    timestamp.hour + timestamp.minute/60 + timestamp.second/3600)
    #  Example: compute Sun longitude
    sun_long = swe.calc_ut(jd, swe.SUN)[0]
    #  TODO: implement each bala component
    return {"sun_long": sun_long}
