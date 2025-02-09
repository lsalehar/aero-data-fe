import logging
from typing import Optional

import supabase as sb
from postgrest.types import ReturnMethod

import reflex as rx
from aero_data import db_client

logger = logging.getLogger()


def log_event(
    event_type: str,
    sid: str,
    event_details: Optional[dict] = None,
    db_client: sb.Client = db_client,
):
    try:
        db_client.table("event_logs").insert(
            {
                "event_type": event_type,
                "event_details": event_details,
                "session_id": sid,
                "is_prod": rx.app.is_prod_mode(),
            },
            returning=ReturnMethod.minimal,
        ).execute()
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
