"""OpenAir file format parsing and conversion utilities."""

import json
import re
from typing import Any

from aero_data.utils.units import interpolate_circle, parse_openair_latlon


def _parse_openair_latlon(latlon: str) -> tuple[float, float]:
    """Parse a lat/lon in DMS or DDM format as used in OpenAir.

    Returns:
        tuple[float, float]: (lat, lon) in decimal degrees.

    """
    # Matches both DMS and DDM, e.g. 46:19:13.0000 N 014:22:12.0000 E
    pattern = re.compile(
        r"(\d+):(\d+):([\d\.]+)[ ]?([NS])[\s,]+(\d+):(\d+):([\d\.]+)[ ]?([EW])",
    )
    match = pattern.match(latlon)
    if not match:
        msg = f"Invalid DP coordinate: {latlon}"
        raise ValueError(msg)
    lat_d, lat_m, lat_s, lat_h, lon_d, lon_m, lon_s, lon_h = match.groups()
    lat = dms_to_dd(float(lat_d), float(lat_m), float(lat_s))
    lon = dms_to_dd(float(lon_d), float(lon_m), float(lon_s))
    if lat_h == "S":
        lat = -lat
    if lon_h == "W":
        lon = -lon
    return lat, lon


def dms_to_dd(d: float, m: float, s: float) -> float:
    """Convert degrees, minutes, seconds to decimal degrees."""
    return d + m / 60 + s / 3600


def _save_current_airspace(
    current: dict[str, Any],
    coords: list[tuple[float, float]],
    aa_times: list[str],
    circle_center: tuple[float, float] | None,
    circle_radius_nm: float | None,
    airspaces: list[dict[str, Any]],
) -> tuple[
    list[tuple[float, float]],
    list[str],
    tuple[float, float] | None,
    float | None,
]:
    """Save current airspace and reset state."""
    if current and (coords or circle_center):
        if coords:
            current["geometry"] = coords
        elif circle_center and circle_radius_nm is not None:
            current["circle"] = (circle_center, circle_radius_nm)
        if aa_times:
            current.setdefault("properties", {})["activation_times"] = aa_times.copy()
        airspaces.append(current)
    return [], [], None, None


def _process_property_line(line: str, current: dict[str, Any]) -> None:
    """Process property lines (AC, AN, AY, AF, AG, AL, AH)."""
    prefix_map = {
        "AC": "class",
        "AN": "name",
        "AY": "type",
        "AF": "frequency",
        "AG": "station",
        "AL": "lower_limit",
        "AH": "upper_limit",
    }
    for prefix, prop in prefix_map.items():
        if line.startswith(prefix):
            current["properties"][prop] = line[3:].strip()
            break


def _process_coordinate_line(
    line: str,
    coords: list[tuple[float, float]],
    aa_times: list[str],
    circle_center: tuple[float, float] | None,
    circle_radius_nm: float | None,
) -> tuple[
    list[tuple[float, float]],
    list[str],
    tuple[float, float] | None,
    float | None,
]:
    """Process coordinate-related lines (AA, V X=, DP, DC)."""
    if line.startswith("AA"):
        aa_times.append(line[3:].strip())
    elif line.startswith("V X="):
        center_str = line[4:].strip()
        circle_center = parse_openair_latlon(center_str)
    elif line.startswith("DP"):
        latlon = line[3:].strip()
        lat, lon = parse_openair_latlon(latlon)
        coords.append((lon, lat))  # GeoJSON: (lon, lat)
    elif line.startswith("DC"):
        try:
            radius_nm = float(line[3:].strip())
        except ValueError:
            radius_nm = None
        if circle_center and radius_nm is not None:
            circle_radius_nm = radius_nm
    return coords, aa_times, circle_center, circle_radius_nm


def _process_openair_line(
    line: str,
    current: dict[str, Any],
    coords: list[tuple[float, float]],
    aa_times: list[str],
    circle_center: tuple[float, float] | None,
    circle_radius_nm: float | None,
) -> tuple[
    list[tuple[float, float]],
    list[str],
    tuple[float, float] | None,
    float | None,
]:
    """Process a single OpenAir line and update state."""
    if line.startswith(("AC", "AN", "AY", "AF", "AG", "AL", "AH")):
        _process_property_line(line, current)
    else:
        coords, aa_times, circle_center, circle_radius_nm = _process_coordinate_line(
            line,
            coords,
            aa_times,
            circle_center,
            circle_radius_nm,
        )
    return coords, aa_times, circle_center, circle_radius_nm


def parse_openair(input_str: str) -> list[dict[str, Any]]:
    """Parse an OpenAir file and return a list of airspace definitions as dicts.

    Supports AA (activation times) and DC (circular area) commands.
    """
    airspaces = []
    current: dict[str, Any] = {"properties": {}, "geometry": []}
    coords: list[tuple[float, float]] = []
    aa_times: list[str] = []
    circle_center: tuple[float, float] | None = None
    circle_radius_nm: float | None = None

    for raw_line in input_str.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue
        if line.startswith("AC"):
            coords, aa_times, circle_center, circle_radius_nm = _save_current_airspace(
                current,
                coords,
                aa_times,
                circle_center,
                circle_radius_nm,
                airspaces,
            )
            current = {"properties": {}, "geometry": []}

        coords, aa_times, circle_center, circle_radius_nm = _process_openair_line(
            line,
            current,
            coords,
            aa_times,
            circle_center,
            circle_radius_nm,
        )

    # Final airspace
    _save_current_airspace(
        current,
        coords,
        aa_times,
        circle_center,
        circle_radius_nm,
        airspaces,
    )
    return airspaces


def openair_to_geojson(openair_text: str) -> str:
    """Convert OpenAir text to a GeoJSON FeatureCollection string.

    Supports DP polygons, DC circles, and AA activation times.
    """
    features = []
    airspaces = parse_openair(openair_text)
    for asp in airspaces:
        properties = asp.get("properties", {})
        # Polygon by DP
        if asp.get("geometry"):
            coords = asp["geometry"]
            if coords and coords[0] != coords[-1]:
                coords = [*coords, coords[0]]
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords],
                },
                "properties": properties,
            }
            features.append(feature)
        # Circle by DC
        elif "circle" in asp:
            center, radius_nm = asp["circle"]
            circle_coords = interpolate_circle(center, radius_nm)
            # Ensure closed ring
            if circle_coords[0] != circle_coords[-1]:
                circle_coords.append(circle_coords[0])
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [circle_coords],
                },
                "properties": properties,
            }
            features.append(feature)
    fc = {"type": "FeatureCollection", "features": features}
    return json.dumps(fc, indent=2)


def geojson_to_openair(geojson_str: str) -> str:
    """Convert GeoJSON FeatureCollection string to OpenAir format.

    Only supports polygons with DP points.
    """
    data = json.loads(geojson_str)
    lines = ["*VERSION: 2.0", "*WRITTEN_BY: SeeYou"]
    for feature in data["features"]:
        props = feature.get("properties", {})
        if "class" in props:
            lines.append(f"AC {props['class']}")
        if "type" in props:
            lines.append(f"AY {props['type']}")
        if "name" in props:
            lines.append(f"AN {props['name']}")
        if "frequency" in props:
            lines.append(f"AF {props['frequency']}")
        if "station" in props:
            lines.append(f"AG {props['station']}")
        if "lower_limit" in props:
            lines.append(f"AL {props['lower_limit']}")
        if "upper_limit" in props:
            lines.append(f"AH {props['upper_limit']}")
        coords = feature["geometry"]["coordinates"][0]
        for lon, lat in coords:
            lines.append(f"DP {format_dms(lat, 'NS')} {format_dms(lon, 'EW')}")
        lines.append("")  # Separate airspaces
    return "\n".join(lines)


def format_dms(deg: float, hemis: str) -> str:
    """Format a decimal degree value as DMS string.

    Args:
        deg: Decimal degrees
        hemis: 'NS' for latitude, 'EW' for longitude

    """
    is_neg = deg < 0
    deg = abs(deg)
    d = int(deg)
    m = int((deg - d) * 60)
    s = (deg - d - m / 60) * 3600
    suffix = ("S" if is_neg else "N") if hemis == "NS" else ("W" if is_neg else "E")
    return f"{d:02}:{m:02}:{s:07.4f}{suffix}"
