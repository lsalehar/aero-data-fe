from aero_data.utils.constants import FT_2_M, ML_2_M, NM_2_M
from aero_data.utils.naviter.constants import (
    CUP_DISTANCE_REGEX,
    CUP_FREQ_REGEX,
    CUP_LAT_FORMAT,
    CUP_LAT_REGEX,
    CUP_LON_FORMAT,
    CUP_LON_REGEX,
    CUP_SYTLE_MAPPING,
)


def convert_lat_lon_to_dd(coord: str) -> float:
    """
    Converts a coordinate string in 'SeeYou' format to decimal degrees.

    :param: str coord: A coordinate string in CUP latitude or longitude format.
    :return: The coordinate in decimal degrees.
    :rtype: float
    """
    if not isinstance(coord, str):
        raise ValueError(f"Invalid type for coordinate: {type(coord)}")

    match = None
    for pattern in (CUP_LAT_REGEX, CUP_LON_REGEX):
        match = pattern.match(coord.strip())
        if match:
            break

    if not match:
        raise ValueError(f"Invalid coordinate format: {coord}")

    degrees, minutes, direction = match.groups()
    degrees = int(degrees)
    minutes = float(minutes)
    direction_multiplier = 1 if direction in ("N", "E") else -1

    return direction_multiplier * (degrees + minutes / 60)


def format_decimal_degrees_to_cup(decimal_degrees: float, is_lat=False) -> str:
    """
    Formats decimal degrees as a CUP style string.
    :param: float decimal_degrees: A coordintate in decimal degrees.
    :param: bool is_lat: Is latitude?
    :rtype: str
    """
    if not isinstance(decimal_degrees, (float, int)):
        raise ValueError(
            f"Invalid type for decimal_degrees: {decimal_degrees} {type(decimal_degrees)}"
        )

    if is_lat:
        direction = "N" if decimal_degrees >= 0 else "S"
    else:
        direction = "E" if decimal_degrees >= 0 else "W"

    degrees = int(abs(decimal_degrees))
    decimal_minutes = (abs(decimal_degrees) - degrees) * 60

    if is_lat:
        return CUP_LAT_FORMAT.format(deg=degrees, dec_min=decimal_minutes, dir=direction)
    return CUP_LON_FORMAT.format(deg=degrees, dec_min=decimal_minutes, dir=direction)


def format_dd_lat_lon_to_cup(lat, lon):
    """
    Formats latitude and longitude from decimal degrees to a CUP-compatible format.

    :param lat: Latitude in decimal degrees (float).
    :param lon: Longitude in decimal degrees (float).
    :return: Tuple of formatted latitude and longitude.
    :raises ValueError: If latitude or longitude are out of bounds.
    :raises TypeError: If latitude or longitude are not numbers.
    """
    # Check for numeric values
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise TypeError("Latitude and longitude must be numeric values.")

    # Check for latitude and longitude bounds
    if not (-90 <= lat <= 90):
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if not (-180 <= lon <= 180):
        raise ValueError("Longitude must be between -180 and 180 degrees.")

    # Format latitude and longitude
    formatted_lat = format_decimal_degrees_to_cup(lat, is_lat=True)
    formatted_lon = format_decimal_degrees_to_cup(lon, is_lat=False)

    return formatted_lat, formatted_lon


def convert_distance_to_m_and_og_unit(dist: str) -> tuple[float, str]:
    """
    Converts an elevation string to a floating-point number in meters and returns the original unit.

    :param dist (str): Elevation string possibly containing 'ft' or 'm'.
    :return: Tuple containing the elevation in meters as a floating-point number and the original unit.
    :rtype: tuple
    """

    if dist.strip() == "":
        return float("-inf"), "m"

    match = CUP_DISTANCE_REGEX.match(dist.strip().lower())
    if not match:
        raise ValueError(f"Invalid distance format: {dist}")

    unit_conversion = {"ft": FT_2_M, "nm": NM_2_M, "ml": ML_2_M, "m": 1}

    value, unit = match.groups()[0], match.groups()[-1].lower()
    if unit not in unit_conversion:
        raise ValueError(f"Unsupported unit: {unit}")

    distance = float(value) * unit_conversion[unit]
    return distance, unit


def format_distance(dist_in_m: float, unit: str) -> str:
    if dist_in_m == float("-inf") or dist_in_m is None:
        return ""

    unit_conversion = {
        "ft": (FT_2_M, "{:.0f}ft"),  # No decimal places for feet
        "nm": (NM_2_M, "{:.2f}nm"),  # Two decimal places for nautical miles
        "ml": (ML_2_M, "{:.2f}ml"),  # Two decimal places for miles
        "m": (1.0, "{:.1f}m"),  # No decimal places for meters
    }

    factor, format_str = unit_conversion.get(unit.lower(), (1.0, "{:.1f}m"))
    distance = dist_in_m / factor

    if unit.lower() == "m" and (distance * 10) % 1 == 0:
        format_str = "{:.0f}m"

    fs = format_str.format(distance)

    return fs


def is_valid_cup_freq(freq: str):
    return bool(CUP_FREQ_REGEX.match(freq))


def is_valid_style(style: str | int):
    if isinstance(style, int) and style in CUP_SYTLE_MAPPING.keys():
        return True
    if isinstance(style, str) and style.isdigit() and int(style) in CUP_SYTLE_MAPPING.keys():
        return True
    return False
