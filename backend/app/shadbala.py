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
# Moon and Mercury are considered benefic while the Sun is treated as neutral.
# Rahu and Ketu are included as malefics when the nodes are added to the
# positions dictionary.
BENEFIC_PLANETS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFIC_PLANETS = {"Mars", "Saturn", "Rahu", "Ketu"}

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
    """Return Drik Bala based on classical Graha Drishti rules.

    The angular separation is measured from the aspecting planet toward the
    planet receiving the aspect.  Only separations that fall within the classical
    aspect angles contribute to the total strength.
    """

    # Remove the planet under consideration from the list of aspecting bodies
    others = {name: lon for name, lon in positions.items() if name != planet}
    if not others:
        return 0.0

    FULL = 60.0  # strength of a full aspect
    TOL = 5.0    # angular tolerance in degrees

    # Aspect angles for Mars, Jupiter and Saturn.  Other planets only aspect the
    # 7th house (180°).  Weights implement the commonly used fractional values
    # for specific aspects.
    ASPECTS: dict[str, dict[int, float]] = {
        "Mars": {90: 1.0, 180: 1.0, 210: 1.0},       # 4th, 7th, 8th
        "Jupiter": {120: 0.6, 180: 1.0, 240: 0.6},   # 5th, 7th, 9th
        "Saturn": {60: 1.0, 180: 1.0, 270: 1.0},     # 3rd, 7th, 10th
    }

    DEFAULT_ASPECT = {180: 1.0}

    total = 0.0
    for name, other in others.items():
        # measure from the source planet (other) to the target planet (plon)
        diff = (plon - other + 360.0) % 360.0
        aspects = ASPECTS.get(name, DEFAULT_ASPECT)
        for angle, weight in aspects.items():
            if abs(diff - angle) <= TOL:
                strength = FULL * weight
                if name in BENEFIC_PLANETS:
                    total += strength
                elif name in MALEFIC_PLANETS:
                    total -= strength
                # The Sun is treated as neutral
                break

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
    # Include the lunar nodes so they contribute to Drik bala calculations
    positions["Rahu"] = rahu_lon
    positions["Ketu"] = ketu_lon

    for name, pos in positions.items():
        if name in results:
            results[name]["drik"] = _drik_bala(pos, name, positions)

    return results


def _varga_sign(longitude: float, varga: int) -> int:
    """Return the sign index (0..11) for a given varga division."""
    return int(math.floor(longitude * varga / 30.0)) % 12


_SIGN_RULER = [
    "Mars",
    "Venus",
    "Mercury",
    "Moon",
    "Sun",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Saturn",
    "Jupiter",
]

_MASCULINE_PLANETS = {"Sun", "Mars", "Jupiter", "Saturn"}
_DIURNAL_PLANETS = {"Sun", "Jupiter", "Saturn"}


def _saptavargaja_bala(longitude: float, planet: str) -> float:
    """Strength from dignity across seven classical vargas."""
    exalt_sign = int(EXALTATION_DEGREES[planet] // 30)
    total = 0.0
    for varga in (1, 2, 3, 9, 12, 30, 60):
        sign = _varga_sign(longitude, varga)
        ruler = _SIGN_RULER[sign]
        if ruler == planet or sign == exalt_sign:
            total += 5.0
    return total


def _ojayugmadi_bala(longitude: float, planet: str) -> float:
    sign = int(longitude // 30) + 1
    if sign % 2 == 1 and planet in _MASCULINE_PLANETS:
        return 15.0
    return 0.0


def _house_position(jd: float, lat: float, lon: float, planet_long: float) -> int:
    """Return the house position using Swiss Ephemeris if available."""
    try:
        cusps, _ = swe.houses(jd, lat, lon)
    except Exception:
        return int(planet_long % 360 // 30) + 1
    lon_norm = planet_long % 360
    for i in range(12):
        start = cusps[i] % 360
        end = cusps[(i + 1) % 12] % 360
        if end < start:
            end += 360
        if start <= lon_norm < end:
            return i + 1
    return 12


def _kendradi_bala(jd: float, lat: float, lon: float, planet_long: float) -> float:
    house = _house_position(jd, lat, lon, planet_long)
    if house in {1, 4, 7, 10}:
        return 60.0
    if house in {2, 5, 8, 11}:
        return 30.0
    return 15.0


def _drekkana_bala(longitude: float, planet: str) -> float:
    sign = int(longitude // 30)
    deg = longitude % 30
    idx = int(deg // 10)
    if idx == 0:
        ruler = _SIGN_RULER[sign]
    elif idx == 1:
        ruler = _SIGN_RULER[(sign + 4) % 12]
    else:
        ruler = _SIGN_RULER[(sign + 8) % 12]
    return 15.0 if ruler == planet else 0.0


def _paksha_bala(moon_lon: float, sun_lon: float) -> float:
    diff = _angle_diff(moon_lon, sun_lon)
    return 60.0 * diff / 180.0


def _nathonnatha_bala(lat_deg: float) -> float:
    ratio = min(1.0, abs(lat_deg) / 30.0)
    return 60.0 * ratio


def _tribhaga_bala(timestamp: datetime, lat: float, lon: float, planet: str) -> float:
    jd_date = swe.julday(timestamp.year, timestamp.month, timestamp.day, 0.0)
    try:
        sr = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_RISE)[1]
        ss = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_SET)[1]
    except Exception:
        sr = jd_date + 0.25
        ss = jd_date + 0.75
    jd_now = swe.julday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600,
    )
    if sr <= jd_now < ss:
        part = (ss - sr) / 3.0
        if jd_now < sr + part:
            return 60.0
        if jd_now < sr + 2 * part:
            return 30.0
        return 15.0
    else:
        sr_prev = sr - 1.0
        part = (sr - ss) / 3.0
        if jd_now < ss + part:
            return 60.0
        if jd_now < ss + 2 * part:
            return 30.0
        return 15.0


def _ayana_bala(sun_long: float, planet: str) -> float:
    north = sun_long < 180.0
    if planet in _DIURNAL_PLANETS and north:
        return 60.0
    if planet not in _DIURNAL_PLANETS and not north:
        return 60.0
    return 30.0


def _varshadi_bala(timestamp: datetime, planet: str) -> float:
    return 15.0 if WEEKDAY_LORD[timestamp.weekday()] == planet else 0.0


def _hora_bala(timestamp: datetime, lat: float, lon: float, planet: str) -> float:
    return _kala_bala(timestamp, lat, lon, planet)


def _yamardha_bala(timestamp: datetime, lat: float, lon: float, planet: str) -> float:
    jd_date = swe.julday(timestamp.year, timestamp.month, timestamp.day, 0.0)
    try:
        sr = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_RISE)[1]
        ss = swe.rise_trans(jd_date, swe.SUN, lon, lat, swe.CALC_SET)[1]
    except Exception:
        sr = jd_date + 0.25
        ss = jd_date + 0.75
    jd_now = swe.julday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600,
    )
    day_len = ss - sr
    if sr <= jd_now < ss:
        part = day_len / 8.0
        index = int((jd_now - sr) / part)
    else:
        part = (sr + 1 - ss) / 8.0
        index = int((jd_now - ss) / part)
    if index in {0, 7} and planet == "Saturn":
        return 30.0
    if index in {3, 4} and planet == "Sun":
        return 30.0
    return 15.0


def compute_shadbala(timestamp: datetime, lat: float, lon: float, use_true_node: bool = False):
    """Return full Shadbala values including all sub components."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600,
    )
    positions: dict[str, float] = {}
    latitudes: dict[str, float] = {}
    speeds: dict[str, float] = {}
    results: dict[str, dict[str, float]] = {}

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
        latitudes[name] = lat_deg
        speeds[name] = speed

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
    positions["Rahu"] = rahu_lon
    positions["Ketu"] = ketu_lon

    sun_long = positions["Sun"]
    moon_long = positions["Moon"]

    for name in [p[0] for p in PLANETS]:
        lon_deg = positions[name]
        lat_deg = latitudes[name]
        sthana = (
            _uccha_bala(lon_deg, name)
            + _saptavargaja_bala(lon_deg, name)
            + _ojayugmadi_bala(lon_deg, name)
            + _kendradi_bala(jd, lat, lon, lon_deg)
            + _drekkana_bala(lon_deg, name)
        )
        dig = _dig_bala(jd, lat, lon, lon_deg, name)
        kala = (
            _hora_bala(timestamp, lat, lon, name)
            + _paksha_bala(moon_long, sun_long) if name == "Moon" else _hora_bala(timestamp, lat, lon, name)
        )
        if name == "Moon":
            kala += _paksha_bala(moon_long, sun_long)
        kala += _nathonnatha_bala(lat_deg)
        kala += _tribhaga_bala(timestamp, lat, lon, name)
        kala += _ayana_bala(sun_long, name)
        kala += _varshadi_bala(timestamp, name)
        kala += _yamardha_bala(timestamp, lat, lon, name)
        cheshta = _cheshta_bala(speeds[name], name)
        naisargika = NAISARGIKA_BALA[name]
        drik = _drik_bala(lon_deg, name, positions)
        total = sthana + dig + kala + cheshta + naisargika + drik
        results[name] = {
            "sthāna": sthana,
            "dig": dig,
            "kāla": kala,
            "cheshta": cheshta,
            "naisargika": naisargika,
            "drik": drik,
            "total": total,
        }

    return results
