from datetime import datetime
import math
import swisseph as swe

# Use sidereal calculations with the Lahiri ayanamsa
swe.set_sid_mode(swe.SIDM_LAHIRI)

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

# Simple benefic/malefic categorisation used for Drik bala
BENEFIC_PLANETS = {"Jupiter", "Venus"}
MALEFIC_PLANETS = {"Mars", "Saturn"}


def _angle_diff(a: float, b: float) -> float:
    """Return the absolute difference between two angles within 0..180."""
    diff = (a - b) % 360.0
    if diff > 180:
        diff = 360 - diff
    return diff


def _uccha_bala(longitude: float, planet: str) -> float:
    diff = _angle_diff(longitude, EXALTATION_DEGREES[planet])
    return 60.0 * (180.0 - diff) / 180.0


def _dig_bala(jd: float, lat: float, lon: float, planet_long: float, planet: str) -> float:
    """Directional strength using actual house position."""
    try:
        cusps, _ = swe.houses(jd, lat, lon)
    except Exception:
        # Fallback to sign-based house if house computation fails
        house = int(planet_long % 360 // 30) + 1
    else:
        # Determine which house the planet occupies
        house = 12
        lon_norm = planet_long % 360
        for i in range(12):
            start = cusps[i] % 360
            end = cusps[(i + 1) % 12] % 360
            if end < start:
                end += 360
            if start <= lon_norm < end:
                house = i + 1
                break

    diff = abs(house - DIRECTIONAL_HOUSE[planet])
    if diff > 6:
        diff = 12 - diff
    if diff > 6:
        return 0.0
    return 60.0 * (6 - diff) / 6


def _kala_bala(timestamp: datetime, lat: float, lon: float, planet: str) -> float:
    """Time strength based on day/night fraction."""
    jd_date = swe.julday(timestamp.year, timestamp.month, timestamp.day, 0.0)
    try:
        sr = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_RISE)[1]
        ss = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_SET)[1]
    except Exception:
        # Fallback to naive 6am/6pm times if ephemeris is unavailable
        sr = jd_date + 0.25
        ss = jd_date + 0.75
    jd_now = swe.julday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600,
    )

    if sr < ss:
        day_frac = min(max((jd_now - sr) / (ss - sr), 0.0), 1.0) if sr <= jd_now < ss else 0.0
    else:
        day_frac = 0.5

    is_day = sr <= jd_now < ss if sr < ss else True

    if planet in ["Sun", "Jupiter", "Saturn"]:
        return 60.0 * day_frac
    elif planet in ["Moon", "Mars", "Venus"]:
        return 60.0 * (1.0 - day_frac)
    else:  # Mercury, treat as neutral
        balance = 1.0 - abs(0.5 - day_frac) * 2
        return 30.0 + 30.0 * balance


def _cheshta_bala(speed: float, planet: str) -> float:
    max_speed = MAX_SPEED.get(planet, 1.0)
    ratio = abs(speed) / max_speed
    return ratio * 60.0


def _drik_bala(plon: float, others: dict[str, float]) -> float:
    """Aspect strength based on separations from other planets.

    Benefic aspects contribute positively while malefic aspects reduce the score.
    """
    if not others:
        return 0.0
    total = 0.0
    for name, other in others.items():
        diff = _angle_diff(plon, other)
        strength = max(0.0, 60.0 - diff / 3.0)
        if name in MALEFIC_PLANETS:
            strength *= -1
        total += strength
    return total / len(others)


def row(timestamp: datetime, lat: float, lon: float):
    """Return dict of {planet: {uccha, dig, kala, cheshta, naisargika, drik}}."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600,
    )
    results = {}
    positions: dict[str, float] = {}

    for name, pid in PLANETS:
        calc_result = swe.calc_ut(jd, pid)
        if (
            isinstance(calc_result, tuple)
            and len(calc_result) == 2
            and isinstance(calc_result[0], (list, tuple))
        ):
            lon_deg, lat_deg, dist, speed = calc_result[0][:4]
        else:
            lon_deg, lat_deg, dist, speed = calc_result[:4]
        positions[name] = lon_deg
        results[name] = {
            "uccha": _uccha_bala(lon_deg, name),
            "dig": _dig_bala(jd, lat, lon, lon_deg, name),
            "kala": _kala_bala(timestamp, lat, lon, name),
            "cheshta": _cheshta_bala(speed, name),
            "naisargika": NAISARGIKA_BALA[name],
            "drik": 0.0,
        }

    for name, pos in positions.items():
        others = {pname: p for pname, p in positions.items() if pname != name}
        results[name]["drik"] = _drik_bala(pos, others)

    return results
