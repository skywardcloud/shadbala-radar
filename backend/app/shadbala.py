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
# Moon and Mercury are considered benefic here while the Sun is treated as
# neutral. Rahu and Ketu are currently ignored.
BENEFIC_PLANETS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC_PLANETS = {"Mars", "Saturn"}

# Mapping of Python weekday numbers (Monday=0) to planetary lords
WEEKDAY_LORD = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun",      # Sunday
}

# Order of hora lords used for the repeating sequence
HORA_SEQUENCE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

# Simplified friendship table for hora relationships
HORA_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}


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
    """Time strength using unequal horas and friendship."""
    jd_date = swe.julday(timestamp.year, timestamp.month, timestamp.day, 0.0)

    try:
        sr = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_RISE)[1]
        ss = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_SET)[1]
        sr_next = swe.rise_trans(jd_date + 1, swe.SUN, lon, lat, swe.CALC_RISE)[1]
        ss_prev = swe.rise_trans(jd_date - 1, swe.SUN, lon, lat, swe.CALC_SET)[1]
    except Exception:
        # Fallback to naive 6am/6pm times if ephemeris is unavailable
        sr = jd_date + 0.25
        ss = jd_date + 0.75
        sr_next = sr + 1.0
        ss_prev = ss - 1.0

    jd_now = swe.julday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600,
    )

    if sr <= jd_now < ss:
        hora_len = (ss - sr) / 12.0
        hora_index = int((jd_now - sr) / hora_len)
    elif jd_now >= ss:
        hora_len = (sr_next - ss) / 12.0
        hora_index = 12 + int((jd_now - ss) / hora_len)
    else:  # before sunrise
        hora_len = (sr - ss_prev) / 12.0
        hora_index = 12 + int((jd_now - ss_prev) / hora_len)

    weekday_lord = WEEKDAY_LORD[timestamp.weekday()]
    start_idx = HORA_SEQUENCE.index(weekday_lord)
    hora_lord = HORA_SEQUENCE[(start_idx + hora_index) % 7]

    if planet == hora_lord:
        return 60.0
    if planet in HORA_FRIENDS.get(hora_lord, set()):
        return 45.0
    return 30.0


def _cheshta_bala(speed: float, planet: str) -> float:
    max_speed = MAX_SPEED.get(planet, 1.0)
    ratio = abs(speed) / max_speed
    return ratio * 60.0


def _drik_bala(plon: float, planet: str, positions: dict[str, float]) -> float:
    """Aspect strength considering benefic or malefic nature of other planets."""

    others = {name: lon for name, lon in positions.items() if name != planet}
    if not others:
        return 0.0

    total = 0.0
    for name, other in others.items():
        diff = _angle_diff(plon, other)
        strength = max(0.0, 60.0 - diff / 3.0)
        if name in BENEFIC_PLANETS:
            total += strength
        elif name in MALEFIC_PLANETS:
            total -= strength
    return total


def row(timestamp: datetime, lat: float, lon: float, use_true_node: bool = False):
    """Return dict of {planet: {uccha, dig, kala, cheshta, naisargika, drik}}.

    Parameters
    ----------
    timestamp : datetime
        Moment for which the planetary strengths are computed.
    lat : float
        Latitude of the observer.
    lon : float
        Longitude of the observer.
    use_true_node : bool, optional
        If ``True`` use the true node for Rahu/Ketu calculations, otherwise the
        mean node is used. Rahu and Ketu are not returned in the result but may
        be added to the internal positions dictionary for Drik bala purposes.
    """
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

    # Calculate Rahu and Ketu positions if needed. They are not included in the
    # returned results by default but can be injected into ``positions`` when
    # Drik bala calculations should consider the lunar nodes.
    node_pid = swe.TRUE_NODE if use_true_node else swe.MEAN_NODE
    node_calc = swe.calc_ut(jd, node_pid)
    if (
        isinstance(node_calc, tuple)
        and len(node_calc) == 2
        and isinstance(node_calc[0], (list, tuple))
    ):
        rahu_lon = node_calc[0][0]
    else:
        rahu_lon = node_calc[0]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    # Uncomment the following lines to include the nodes in Drik bala
    # positions["Rahu"] = rahu_lon
    # positions["Ketu"] = ketu_lon

    for name, pos in positions.items():
        results[name]["drik"] = _drik_bala(pos, name, positions)

    return results
