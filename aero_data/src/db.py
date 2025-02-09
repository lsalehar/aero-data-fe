import logging
from datetime import datetime
from itertools import count
from typing import Dict, List, Tuple
from unittest import result

from postgrest.exceptions import APIError
from shapely import Point

from aero_data import db_client
from aero_data.models import Airport

logger = logging.getLogger(__name__)


def get_last_update(categroy: str = "airports") -> datetime | None:
    try:
        response = (
            db_client.table("updates")
            .select("timestamp")
            .eq("category", categroy)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return datetime.fromisoformat(response.data[0]["timestamp"])
        else:
            logger.warning("No updates for airports found.")
            return None
    except APIError as e:
        logger.exception(f"Exepiton occured while fetching last update: {e}")
        return None


def get_last_update_and_details(category: str = "airports") -> dict | None:
    try:
        response = (
            db_client.table("updates")
            .select("*")
            .eq("category", category)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        else:
            logger.warning("No updates for airports found.")
            return None
    except APIError as e:
        logger.exception(f"Exepiton occured while fetching last update: {e}")
        return None


def get_nearest_airport(location: Point, treshold_m: int):
    fn_name = "get_nearby_airports"
    params_dict = {"lon": location.x, "lat": location.y, "threshold": 2000}
    result = db_client.rpc(fn_name, params=params_dict).execute()
    return result.data[0] if result.data else None


def get_nearest_airport_bulk(
    locations: list[Point] | Tuple[Point], treshold_m: int
) -> list[dict] | None:
    points = [{"lon": point.x, "lat": point.y} for point in locations]
    result = db_client.rpc(
        "get_nearby_airports_bulk", params={"points": points, "threshold": treshold_m}
    ).execute()
    return result.data if result.data else None


def get_or_create_airport(airport: Airport) -> Tuple[dict, bool]:
    response = (
        db_client.table("airports").select("*").eq("source_id", airport.source_id).execute()
    )
    if response.data:
        return Airport.deserialize_apt_json(response.data[0]), False  # type: ignore

    response = db_client.table("airports").insert(airport.to_dict()).execute()
    airport.id = response.data[0]["id"]
    return airport, True  # type: ignore


def get_apts_in_bbox(
    bbox: tuple | list,
    exclude_source_ids: list | None = None,
    exclude_apt_types: list | None = None,
):
    parameters = {
        "min_lon": bbox[0],
        "min_lat": bbox[1],
        "max_lon": bbox[2],
        "max_lat": bbox[3],
    }
    if isinstance(exclude_source_ids, (list, tuple)) and exclude_source_ids:
        parameters.update(exclude_ids=exclude_source_ids)
    if isinstance(exclude_apt_types, (list, tuple)) and exclude_apt_types:
        parameters.update(exclude_apt_types=exclude_apt_types)
    response = db_client.rpc("get_airports_in_bbox", params=parameters).execute()
    return response.data if response.data else None


def fetch_all_data(table: str, select: str, chunk_size: int = 1000) -> List[Dict]:
    """Fetch all data from a database table in chunks."""
    logger.info("Fetching data from DB...")
    all_data = []
    for offset in count(step=chunk_size):
        response = (
            db_client.table("airports")
            .select(select)
            .range(offset, offset + chunk_size - 1)
            .execute()
        )
        data_chunk = response.data or []
        all_data.extend(data_chunk)

        if len(data_chunk) < chunk_size:
            break
    return all_data
