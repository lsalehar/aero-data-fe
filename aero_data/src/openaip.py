from typing import Any, Dict, List

from aero_data import countries
from aero_data.models import Airport, Country
from aero_data.utils.openaip.constants import AirportType
from aero_data.utils.openaip.utils import (
    get_airport_cup_style,
    get_elevation,
    get_main_radio,
    get_main_rwy,
    get_point,
    get_radio_frequency,
    get_rwy_heading,
    get_rwy_length,
    get_rwy_width,
)


def filter_by_type(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters out items with heliports and water aerodromes.
    """
    return [item for item in data if item.get("type") not in (4, 7, 10)]


def construct_airport_from_oap(oap_airport: dict):
    """
    Constructs an Airport object from OAP airport data.

    Args:
        oap_airport (dict): Dictionary containing OAP airport details.

    Returns:
        Airport: The constructed Airport object.
    """
    main_rwy = get_main_rwy(oap_airport.get("runways", {}))
    main_radio = get_main_radio(oap_airport.get("frequencies", {}))
    rw_len = get_rwy_length(main_rwy)
    rw_width = get_rwy_width(main_rwy)

    airport = Airport(
        name=oap_airport.get("name", "").title(),
        code=oap_airport.get("icaoCode", ""),
        country=countries.get_by_iso2(oap_airport.get("country", "")),
        location=get_point(oap_airport.get("geometry", {})),
        elev=get_elevation(oap_airport.get("elevation", {})),
        style=get_airport_cup_style(oap_airport),
        apt_type=AirportType(oap_airport.get("type", 999)),
        rw_dir=get_rwy_heading(main_rwy),
        rw_len=None if rw_len == 0 else rw_len,
        rw_width=None if rw_width == 0 else rw_width,
        freq=get_radio_frequency(main_radio),
        source_id=oap_airport.get("_id", None),
    )

    return airport
