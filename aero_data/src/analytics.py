import logging

import reflex as rx
import supabase as sb
from postgrest.types import ReturnMethod

from aero_data import db_client

logger = logging.getLogger()


def log_event(
    event_type: str,
    sid: str,
    event_details: dict | None = None,
    db_client: sb.Client = db_client,
):
    try:
        db_client.table("event_logs").insert(
            {
                "event_type": event_type,
                "event_details": event_details,
                "session_id": sid,
                "is_prod": rx.app.is_prod_mode(),  # type: ignore
            },
            returning=ReturnMethod.minimal,
        ).execute()
    except Exception as e:
        logger.error(f"Failed to log event: {e}")


def get_unique_visits(db_client: sb.Client = db_client) -> int:
    try:
        result = db_client.rpc("count_unique_page_visits").execute()
        return result.data if result.data else 0
    except Exception as e:
        logger.error(f"Failed to get page visits: {e}")
        return 0


def get_nr_updates():
    try:
        result = db_client.rpc("count_cup_updates").execute()
        return result.data if result.data else 0
    except Exception as e:
        logger.error(f"Failed to get # cup updates: {e}")
        return 0
