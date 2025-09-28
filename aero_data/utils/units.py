import json
import math
import re
from typing import Any, Dict, Iterator, List, Tuple


def dms_to_dd(d: float, m: float, s: float) -> float:
    return d + m / 60 + s / 3600


def parse_dms_coord(coord_str: str) -> float:
    parts = coord_str.strip().split(":")
    if len(parts) != 3:
        raise ValueError("DMS coordinate must be in D:M:S format")
    return dms_to_dd(float(parts[0]), float(parts[1]), float(parts[2]))


def find_eapi_coords(text: str) -> Iterator[Tuple[float, float]]:
    """
    Find and yield all eAPI-style coordinates from a text blob.
    Example match: 46 10 29 N 013 39 58 E
    """
    pattern = re.compile(r"(\d+)\s+(\d+)\s+(\d+)\s+([NS])\s+(\d+)\s+(\d+)\s+(\d+)\s+([EW])")
    for match in pattern.finditer(text):
        lat_d, lat_m, lat_s, lat_h, lon_d, lon_m, lon_s, lon_h = match.groups()
        lat = dms_to_dd(float(lat_d), float(lat_m), float(lat_s))
        lon = dms_to_dd(float(lon_d), float(lon_m), float(lon_s))
        if lat_h == "S":
            lat = -lat
        if lon_h == "W":
            lon = -lon
        yield (lon, lat)


def parse_aip_point(aip_str: str) -> tuple[float, float]:
    """
    Parse an AIP-style coordinate string to (lat, lon) in decimal degrees.

    Args:
        aip_str: String like '455404.3N 0153113.7E'

    Returns:
        Tuple of (latitude, longitude) in decimal degrees.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    # Pattern for AIP: DDDMMSS.sH DDDMMSS.sH (e.g., 455404.3N 0153113.7E)
    pattern = re.compile(
        r"(\d{2,3})(\d{2})(\d{2}(?:\.\d+)?)([NS])\s+(\d{2,3})(\d{2})(\d{2}(?:\.\d+)?)([EW])"
    )
    match = pattern.match(
        aip_str.replace("°", "").replace("'", "").replace('"', "").replace(" ", "")
    )
    if not match:
        # Try matching with spaces between components
        match = re.match(
            r"(\d{2,3})(\d{2})(\d{2}(?:\.\d+)?)([NS])\s+(\d{2,3})(\d{2})(\d{2}(?:\.\d+)?)([EW])",
            aip_str.replace("°", "").replace("'", "").replace('"', ""),
        )
    if not match:
        raise ValueError("Invalid AIP coordinate format. Example: '455404.3N 0153113.7E'")

    lat_d, lat_m, lat_s, lat_h, lon_d, lon_m, lon_s, lon_h = match.groups()
    lat = dms_to_dd(float(lat_d), float(lat_m), float(lat_s))
    lon = dms_to_dd(float(lon_d), float(lon_m), float(lon_s))

    if lat_h == "S":
        lat = -lat
    if lon_h == "W":
        lon = -lon

    return (lat, lon)


def parse_line_to_lon_lat(line: str) -> Tuple[float, float]:
    """
    Parse 'DP DD:MM:SSN DDD:MM:SSE' or 'DP DD:MM:SS N DDD:MM:SS E' into (lon, lat).
    Only accepts lines starting with DP.
    """
    line = line.strip()
    if not line.upper().startswith("DP "):
        raise ValueError("Line must start with 'DP'.")

    # Remove 'DP' and split
    body = line[2:].strip()
    # Try to match both forms in one regex
    match = re.match(
        r"(\d+:\d+:\d+(?:\.\d+)?)([NS]?)\s*([NS])?\s+(\d+:\d+:\d+(?:\.\d+)?)([EW]?)\s*([EW])?",
        body,
    )
    if not match:
        raise ValueError(
            "DP line must be 'DP DD:MM:SSN DDD:MM:SSE' or 'DP DD:MM:SS N DDD:MM:SS E'."
        )

    # Group extraction
    lat_dms, lat_dir1, lat_dir2, lon_dms, lon_dir1, lon_dir2 = match.groups()
    lat_dir = (lat_dir1 or lat_dir2 or "").upper()
    lon_dir = (lon_dir1 or lon_dir2 or "").upper()

    def dms_to_dd(dms: str, direction: str) -> float:
        d, m, s = map(float, dms.split(":"))
        val = d + m / 60 + s / 3600
        if direction in ("S", "W"):
            val = -val
        return val

    lat = dms_to_dd(lat_dms, lat_dir)
    lon = dms_to_dd(lon_dms, lon_dir)
    return (lon, lat)


def parse_eapi_line(line: str) -> tuple[float, float]:
    """
    Parse an eAPI line like '46 10 29 N 013 39 58 E' to (lon, lat).
    """
    pattern = re.compile(r"(\d+)\s+(\d+)\s+(\d+)\s+([NS])\s+(\d+)\s+(\d+)\s+(\d+)\s+([EW])")
    match = pattern.match(line.strip())
    if not match:
        raise ValueError("Invalid eAPI coordinate format")
    lat_d, lat_m, lat_s, lat_h, lon_d, lon_m, lon_s, lon_h = match.groups()
    lat = dms_to_dd(float(lat_d), float(lat_m), float(lat_s))
    lon = dms_to_dd(float(lon_d), float(lon_m), float(lon_s))
    if lat_h == "S":
        lat = -lat
    if lon_h == "W":
        lon = -lon
    return (lon, lat)


def parse_line_to_lon_lat_any(line: str) -> tuple[float, float]:
    """Try all supported coordinate formats."""
    try:
        return parse_line_to_lon_lat(line)
    except Exception:
        pass
    try:
        return parse_aip_point(line)
    except Exception:
        pass
    try:
        return parse_eapi_line(line)
    except Exception:
        pass
    raise ValueError("Could not parse line as DP, AIP, or eAPI coordinate")


def extract_all_supported_coords(text: str) -> list[tuple[float, float]]:
    """Extracts all supported coordinate formats from a blob."""
    coords = []

    # ICAO compact format
    coords.extend(find_icao_compact_coords(text))

    # eAPI: 46 10 29 N 013 39 58 E
    coords.extend(find_eapi_coords(text))

    # Add other formats as needed (e.g., AIP 455404.3N 0153113.7E)
    # coords.extend(find_aip_coords(text))

    # Remove duplicates, keep order (optional)
    seen = set()
    unique_coords = []
    for c in coords:
        if c not in seen:
            unique_coords.append(c)
            seen.add(c)
    return unique_coords


def find_icao_compact_coords(text: str) -> List[Tuple[float, float]]:
    """
    Find and decode compact ICAO coordinates like 461010N 0144103E from a text blob.
    Returns a list of (lon, lat) tuples for GeoJSON (GeoJSON order: [lon, lat]).
    """
    pattern = re.compile(r"(\d{6})([NS])\s+(\d{7})([EW])")
    coords = []
    for match in pattern.finditer(text):
        lat_str, lat_h, lon_str, lon_h = match.groups()
        lat = int(lat_str[:2]) + int(lat_str[2:4]) / 60 + int(lat_str[4:6]) / 3600
        lon = int(lon_str[:3]) + int(lon_str[3:5]) / 60 + int(lon_str[5:7]) / 3600
        if lat_h == "S":
            lat = -lat
        if lon_h == "W":
            lon = -lon
        coords.append((lon, lat))
    return coords


def icao_coords_to_geojson_polygon(text: str) -> str:
    """
    Converts ICAO compact coords text to a GeoJSON Polygon string.
    """
    coords = find_icao_compact_coords(text)
    if not coords:
        raise ValueError("No valid ICAO compact coordinates found.")

    # Auto-close polygon if needed
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    geojson = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [coords]},
        "properties": {},
    }
    return json.dumps(geojson, indent=2)


def fix_geojson_polygons(geojson_str: str) -> str:
    """
    Loads a GeoJSON string, closes all Polygon/MultiPolygon rings if needed, and returns the fixed string.
    """
    with open(geojson_str) as fp:
        data = json.load(fp)

    def close_ring(ring: list[list[float]]) -> list[list[float]]:
        if ring and ring[0] != ring[-1]:
            ring.append(ring[0])
        return ring

    def fix_geometry(geom: dict[str, Any]) -> None:
        if geom["type"] == "Polygon":
            geom["coordinates"] = [close_ring(ring) for ring in geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            geom["coordinates"] = [
                [close_ring(ring) for ring in polygon] for polygon in geom["coordinates"]
            ]
        # Optionally recurse for GeometryCollection

    if data.get("type") == "FeatureCollection":
        for feature in data["features"]:
            fix_geometry(feature["geometry"])
    elif data.get("type") in ("Polygon", "MultiPolygon"):
        fix_geometry(data)
    else:
        raise ValueError("GeoJSON must be a FeatureCollection or (Multi)Polygon.")

    return json.dumps(data, indent=2)


def compact_to_openair(line: str) -> str:
    """
    Convert a single compact eAIP/AIP string (e.g. 455210N 0135035E) to OpenAir DP format.
    Returns a string like 'DP 45:52:10N 013:50:35E'.
    """
    pattern = re.compile(r"(\d{6})([NS])\s*(\d{7})([EW])")
    match = pattern.match(line.strip())
    if not match:
        raise ValueError("Line must be in format 455210N 0135035E")

    lat_raw, lat_h, lon_raw, lon_h = match.groups()
    lat_d, lat_m, lat_s = int(lat_raw[:2]), int(lat_raw[2:4]), int(lat_raw[4:6])
    lon_d, lon_m, lon_s = int(lon_raw[:3]), int(lon_raw[3:5]), int(lon_raw[5:7])
    lat_str = f"{lat_d:02}:{lat_m:02}:{lat_s:02}{lat_h}"
    lon_str = f"{lon_d:03}:{lon_m:02}:{lon_s:02}{lon_h}"
    return f"DP {lat_str} {lon_str}"


def batch_compact_to_openair(text: str) -> List[str]:
    """
    Convert all eAIP/AIP coordinates in a multiline string to OpenAir DP lines.
    Ignores empty lines and invalid lines.
    """
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            lines.append(compact_to_openair(line))
        except Exception:
            continue
    return lines


def parse_openair_latlon(latlon: str) -> Tuple[float, float]:
    """
    Parse a lat/lon in DMS, e.g. 46:19:13.0000 N 014:22:12.0000 E or 46:19:13N 014:22:12E
    """
    pattern = re.compile(
        r"(\d+):(\d+):([\d\.]+)([NS])?\s*([NS])?\s+(\d+):(\d+):([\d\.]+)([EW])?\s*([EW])?"
    )
    m = pattern.match(latlon.replace(",", " "))
    if not m:
        raise ValueError(f"Invalid coordinate: {latlon}")
    lat_d, lat_m, lat_s, lat_h1, lat_h2, lon_d, lon_m, lon_s, lon_h1, lon_h2 = m.groups()
    lat_h = lat_h1 or lat_h2 or ""
    lon_h = lon_h1 or lon_h2 or ""
    lat = dms_to_dd(float(lat_d), float(lat_m), float(lat_s))
    lon = dms_to_dd(float(lon_d), float(lon_m), float(lon_s))
    if lat_h.upper() == "S":
        lat = -lat
    if lon_h.upper() == "W":
        lon = -lon
    return lat, lon


def interpolate_circle(
    center: Tuple[float, float], radius_nm: float, n_points: int = 64
) -> List[Tuple[float, float]]:
    """Generate a circular polygon as a list of (lon, lat) tuples (GeoJSON order)."""
    lat0, lon0 = map(math.radians, center)
    radius_deg = radius_nm / 60  # Roughly, 1 deg lat ≈ 60 NM
    coords = []
    for i in range(n_points + 1):  # +1 to close the ring
        angle = 2 * math.pi * i / n_points
        d_lat = radius_deg * math.cos(angle)
        d_lon = radius_deg * math.sin(angle) / math.cos(lat0)
        lat = math.degrees(lat0 + math.radians(d_lat))
        lon = math.degrees(lon0 + math.radians(d_lon))
        coords.append((lon, lat))
    return coords


def parse_openair(input_str: str) -> List[Dict[str, Any]]:
    """
    Parses an OpenAir file and returns a list of airspace definitions as dicts.
    Supports AA (activation times) and DC (circular area) commands.
    """
    airspaces = []
    current: dict[str, Any] = {}
    coords: list[Tuple[float, float]] = []
    aa_times: list[str] = []
    circle_center: Tuple[float, float] | None = None
    circle_radius_nm: float | None = None

    for line in input_str.splitlines():
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        if line.startswith("AC"):
            # Save previous airspace
            if current and (coords or circle_center):
                if coords:
                    current["geometry"] = coords
                elif circle_center and circle_radius_nm is not None:
                    current["circle"] = (circle_center, circle_radius_nm)
                if aa_times:
                    current.setdefault("properties", {})["activation_times"] = aa_times.copy()
                airspaces.append(current)
                coords = []
                aa_times = []
                circle_center = None
                circle_radius_nm = None
            current = {"properties": {}, "geometry": []}
            current["properties"]["class"] = line[3:].strip()
        elif line.startswith("AN"):
            current["properties"]["name"] = line[3:].strip()
        elif line.startswith("AY"):
            current["properties"]["type"] = line[3:].strip()
        elif line.startswith("AF"):
            current["properties"]["frequency"] = line[3:].strip()
        elif line.startswith("AG"):
            current["properties"]["station"] = line[3:].strip()
        elif line.startswith("AL"):
            current["properties"]["lower_limit"] = line[3:].strip()
        elif line.startswith("AH"):
            current["properties"]["upper_limit"] = line[3:].strip()
        elif line.startswith("AA"):
            aa_times.append(line[3:].strip())
        elif line.startswith("V X="):
            center_str = line[5:].strip()
            circle_center = parse_openair_latlon(center_str)
        elif line.startswith("DP"):
            latlon = line[3:].strip()
            lat, lon = parse_openair_latlon(latlon)
            coords.append((lon, lat))  # GeoJSON: (lon, lat)
        elif line.startswith("DC"):
            try:
                radius_nm = float(line[3:].strip())
            except Exception:
                radius_nm = None
            if circle_center and radius_nm is not None:
                circle_radius_nm = radius_nm

    # Final airspace
    if current and (coords or circle_center):
        if coords:
            current["geometry"] = coords
        elif circle_center and circle_radius_nm is not None:
            current["circle"] = (circle_center, circle_radius_nm)
        if aa_times:
            current.setdefault("properties", {})["activation_times"] = aa_times.copy()
        airspaces.append(current)
    return airspaces


def openair_to_geojson(openair_text: str) -> str:
    """
    Converts OpenAir text to a GeoJSON FeatureCollection string,
    supporting DP polygons, DC circles, and AA activation times.
    """
    features = []
    airspaces = parse_openair(openair_text)
    for asp in airspaces:
        properties = asp.get("properties", {})
        # Polygon by DP
        if "geometry" in asp and asp["geometry"]:
            coords = asp["geometry"]
            if coords and coords[0] != coords[-1]:
                coords = coords + [coords[0]]
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
