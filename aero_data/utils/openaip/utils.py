from typing import Dict, List, Tuple, Union

from shapely.geometry import LineString, Point, Polygon

from aero_data.utils.naviter import CupWaypoint
from aero_data.utils.openaip.constants import RADIO_TYPE_PRIORITY


def get_geometry(geometry: dict) -> Union[Point, LineString, Polygon]:
    """
    Returns appropriate geometry object from geometry dictionary encoded in the json data.

    Parameters:
    geometry (dict): Geometry dictionary
    """

    if not isinstance(geometry, dict):
        raise TypeError(f"Parameter geometry must be 'dict', but is of type '{type(geometry)}'")

    elif geometry.get("type", "") == "Point":
        return Point(*geometry.get("coordinates", []))

    elif geometry.get("type", "") == "LineString":
        return LineString([point for point in geometry.get("coordinates", [])])

    elif geometry.get("type", "") == "Polygon":
        int_coordinates = [(point[0], point[1]) for point in geometry.get("coordinates", [])[0]]
        if len(geometry.get("coordinates", [])) == 2:
            ext_coordinates = [
                (point[0], point[1]) for point in geometry.get("coordinates", [])[1]
            ]
            return Polygon(int_coordinates, ext_coordinates)
        return Polygon(int_coordinates)

    raise ValueError("Invalid geometry type")


def get_point(geometry: dict) -> Point:
    if geometry.get("type", "") != "Point":
        raise ValueError("Invalid geometry type")
    return Point(*geometry.get("coordinates", []))


def get_elevation(elevation: dict) -> int:
    if elevation.get("value") is not None:
        return elevation.get("value")  # type: ignore

    raise ValueError("Invalid elevation value")


def get_coordinates(geometry: dict) -> Tuple[float] | None:
    return geometry.get("coordinates")


def get_rwy_length(runway: dict, default=None):
    return runway.get("dimension", {}).get("length", {}).get("value", default)


def get_rwy_width(runway: dict, default=None):
    return runway.get("dimension", {}).get("width", {}).get("value", default)


def get_rwy_heading(runway: dict) -> int | None:
    if isinstance(runway.get("trueHeading"), str):
        return int(runway.get("trueHeading", ""))
    return runway.get("trueHeading")


def get_rwy_surface(runway: dict) -> int:
    return runway.get("surface", {}).get("mainComposite", 22)


def get_main_rwy(runways: List[Dict]) -> dict:
    if not runways:
        return {}

    main_rwy = None
    max_length = float("-inf")
    for rwy in runways:
        rwy.setdefault("dimension", {})
        rwy.setdefault("surface", {})
        operations = rwy.get("operations")

        if rwy.get("mainRunway") and "operations" == 0:
            return rwy

        length = get_rwy_length(rwy, default=0)
        if length > max_length and operations == 0:
            max_length = length
            main_rwy = rwy

    if main_rwy is None:
        main_rwy = runways[0]

    return main_rwy


def get_airport_cup_style(airport: dict) -> int:
    main_rwy = get_main_rwy(airport.get("runways", []))
    ap_type = airport.get("type")
    main_rwy_sfc = get_rwy_surface(main_rwy)

    # Default cup style
    cup_style = 2

    # Conditions
    is_glider_site = ap_type == 1
    has_main_rwy = main_rwy is not None
    has_solid_surface = main_rwy_sfc in [0, 1, 5]

    if is_glider_site:
        cup_style = 4
    elif has_main_rwy and has_solid_surface:
        cup_style = 5

    return cup_style


def get_radio_frequency(radio: dict) -> str | None:
    return radio.get("value")


def get_radio_description(radio) -> str | None:
    name = radio.get("name", "")
    freq = radio.get("value", "")

    if name and freq:
        return f"{name.title()}: {freq}"
    else:
        return None


def get_main_radio(radios) -> dict:
    if not radios:
        return {}

    for radio in radios:
        if radio.get("primary", False):
            return radio

    radios.sort(key=lambda k: RADIO_TYPE_PRIORITY.get(k.get("type", None)))

    return radios[0]


def cupify_oap_airport(airport: dict, add_radio_to_desc=False) -> CupWaypoint:
    """
    Exports the airport from OAP json in cup format.

    Parameters:
    airport (dict): An OAP airport JSON data

    Returns
    CupWaypoint: CUP Waypoint
    """

    main_rwy = get_main_rwy(airport.get("runways", []))
    main_radio = get_main_radio(airport.get("frequencies", []))

    cup_airport = CupWaypoint(
        name=airport.get("name", ""),
        code=airport.get("icaoCode", ""),
        country=airport.get("country", ""),
        lat=get_geometry(airport.get("geometry")).y,  # type: ignore
        lon=get_geometry(airport.get("geometry")).x,  # type: ignore
        elev=airport.get("elevation", {}).get("value"),
        style=get_airport_cup_style(airport),
        rwdir=get_rwy_heading(main_rwy),
        rwlen=get_rwy_length(main_rwy),
        rwwidth=get_rwy_width(main_rwy),
        freq=get_radio_frequency(main_radio),
        desc=get_radio_description(main_radio) if add_radio_to_desc else None,
    )

    return cup_airport
