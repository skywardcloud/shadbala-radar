from datetime import datetime
import math
import swisseph as swe

# Exaltation degrees for planets
EXALTATION_DEGREES = {
    "Sun": 10,
    "Moon": 33,
    "Mars": 298,
    "Mercury": 165,
    "Jupiter": 95,
    "Venus": 357,
    "Saturn": 200,
}

# House of directional strength for each planet (1..12)
DIRECTIONAL_HOUSE = {
    "Sun": 10,
    "Moon": 4,
    "Mars": 10,
    "Mercury": 1,
    "Jupiter": 1,
    "Venus": 4,
    "Saturn": 7,
}

# Maximum speed used for Cheshta bala normalisation (deg/day)
MAX_SPEED = {
    "Sun": 1.0,
    "Moon": 15.0,
    "Mars": 1.5,
    "Mercury": 2.0,
    "Jupiter": 1.5,
    "Venus": 1.2,
    "Saturn": 1.0,
}

# Naisargika bala values (commonly used constants)
NAISARGIKA_BALA = {
    "Sun": 60.0,
    "Moon": 51.43,
    "Mars": 17.14,
    "Mercury": 25.71,
    "Jupiter": 34.28,
    "Venus": 42.85,
    "Saturn": 8.57,
}

PLANETS = [
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY),
    ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS),
    ("Saturn", swe.SATURN),
]


def _angle_diff(a: float, b: float) -> float:
    """Return the absolute difference between two angles within 0..180."""
    diff = (a - b) % 360.0
    if diff > 180:
        diff = 360 - diff
    return diff


def _uccha_bala(longitude: float, planet: str) -> float:
    diff = _angle_diff(longitude, EXALTATION_DEGREES[planet])
    return 60.0 * (180.0 - diff) / 180.0


def _dig_bala(longitude: float, planet: str) -> float:
    house = int(longitude % 360 // 30) + 1
    diff = abs(house - DIRECTIONAL_HOUSE[planet])
    if diff > 6:
        diff = 12 - diff
    if diff > 6:
        return 0.0
    return 60.0 * (6 - diff) / 6


def _kala_bala(timestamp: datetime) -> float:
    frac = (timestamp.hour + timestamp.minute / 60.0 + timestamp.second / 3600.0) / 24.0
    return 30.0 + 30.0 * math.sin(2 * math.pi * frac)


def _cheshta_bala(speed: float, planet: str) -> float:
    max_speed = MAX_SPEED.get(planet, 1.0)
    ratio = abs(speed) / max_speed
    if ratio > 1.0:
        ratio = 1.0
    return ratio * 60.0


def row(timestamp: datetime, lat: float, lon: float):
    """Return dict of {planet: {uccha, dig, kala, cheshta, naisargika, drik}}."""
    jd = swe.julday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600,
    )

    results = {}
    for name, pid in PLANETS:
        lon_deg, lat_deg, dist, speed = swe.calc_ut(jd, pid)
        results[name] = {
            "uccha": _uccha_bala(lon_deg, name),
            "dig": _dig_bala(lon_deg, name),
            "kala": _kala_bala(timestamp),
            "cheshta": _cheshta_bala(speed, name),
            "naisargika": NAISARGIKA_BALA[name],
            "drik": 0.0,
        }
    return results
