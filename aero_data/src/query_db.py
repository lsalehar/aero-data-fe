import logging
from datetime import datetime
from typing import Tuple

from postgrest.exceptions import APIError
from shapely import Point

from aero_data import db_client

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
