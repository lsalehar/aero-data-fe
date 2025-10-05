import logging
from datetime import datetime

from postgrest.exceptions import APIError
from shapely import Point

from aero_data import db_client

logger = logging.getLogger(__name__)


def get_last_update(category: str = "airports") -> datetime | None:
    try:
        if db_client is None:
            logger.warning("Database client unavailable; cannot fetch last update.")
            return None
        response = (
            db_client.table("updates")
            .select("timestamp")
            .eq("category", category)
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
        logger.exception(f"Exception occurred while fetching last update: {e}")
        return None


def get_last_update_and_details(category: str = "airports") -> dict | None:
    try:
        if db_client is None:
            logger.warning("Database client unavailable; cannot fetch update details.")
            return None
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
        logger.exception(f"Exception occurred while fetching last update: {e}")
        return None


def get_nearest_airport_bulk(
    locations: list[Point] | tuple[Point, ...], threshold_m: int
) -> list[dict] | None:
    if db_client is None:
        logger.warning("Database client unavailable; cannot fetch nearest airports.")
        return None
    points = [{"lon": point.x, "lat": point.y} for point in locations]
    result = db_client.rpc(
        "get_nearby_airports_bulk", params={"points": points, "threshold": threshold_m}
    ).execute()
    return result.data if result.data else None


def get_apts_in_bbox(
    bbox: tuple | list,
    exclude_source_ids: list | None = None,
    exclude_apt_types: list | None = None,
):
    if db_client is None:
        logger.warning("Database client unavailable; cannot fetch airports in bbox.")
        return None
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
