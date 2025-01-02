import json
import logging
import os
from datetime import datetime, timedelta, timezone
from glob import glob
from itertools import count
from typing import Any, Dict, List, Tuple

from decouple import config
from postgrest.exceptions import APIError
from shapely import wkb

from aero_data import countries, db_client
from aero_data.models import Airport
from aero_data.src.query_db import get_last_update
from aero_data.utils.file_handling import load_json, save_raw
from aero_data.utils.general import chunked, has_changed, run_in_threads
from aero_data.utils.google_cloud import GoogleCloudBucket
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

APT_COMPARISON_FIELDS = (
    "name",
    "code",
    "country",
    "location",
    "style",
    "apt_type",
    "rw_dir",
    "rw_len",
    "rw_width",
    "freq",
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

APTS_TABLE = "airports"
UPDATES_TABLE = "updates"
INSERT_CHUNK_SIZE = 10000
DELETE_CHUNK_SIZE = 500


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


def deserialize_apt_json(apt_json: dict, as_dict=False) -> Airport | dict:
    apt = {
        **apt_json,
        "apt_type": AirportType(apt_json.get("apt_type", 999)),
        "country": countries.get_by_iso2(apt_json.get("country", "")),
        "location": wkb.loads(apt_json.get("location", "")),
        "created_at": datetime.fromisoformat(apt_json.get("created_at", None)),
        "updated_at": datetime.fromisoformat(apt_json.get("updated_at", None)),
    }
    return Airport(**apt) if not as_dict else apt


def get_or_create_airport(airport: Airport) -> Tuple[dict, bool]:
    response = (
        db_client.table("airports").select("*").eq("source_id", airport.source_id).execute()
    )
    if response.data:
        return deserialize_apt_json(response.data[0]), False  # type: ignore

    response = db_client.table("airports").insert(airport.to_dict()).execute()
    airport.id = response.data[0]["id"]
    return airport, True  # type: ignore


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


class AirportUpdater:
    CARTEGORY = "airports"

    def __init__(self, last_update: datetime | None = get_last_update()):
        self.oap_airports = []
        self.added_count = 0
        self.updated_count = 0
        self.removed_count = 0
        self.last_update = last_update

    def download_airports(self):
        """Download or load airport data and filter it."""

        # Fix Me: Maybe existing data does not exsist.
        if not self.last_update or datetime.now(timezone.utc) - self.last_update > timedelta(
            days=1
        ):
            oap_airports = self._download_new_airports()
        else:
            oap_airports = self._load_existing_airports()

        self.oap_airports = [construct_airport_from_oap(apt) for apt in oap_airports]

    def _download_new_airports(self) -> List[Dict]:
        logger.info("Downloading new data from OpenAIP...")
        BUCKET = GoogleCloudBucket(config("GCLOUD_BUCKET_NAME"))  # type:ignore
        blobs = [blob for blob in BUCKET.blobs if blob.name.endswith("apt.json")]

        def download_and_process(blob):
            file = BUCKET.download_blob_into_memory(blob)
            save_raw(file, blob.name, "raw_data")
            return filter_by_type(json.loads(file.decode("utf-8")))

        return run_in_threads(download_and_process, blobs)

    def _load_existing_airports(self) -> List[Dict]:
        logger.info("Loading existing data...")
        paths = glob(os.path.join("raw_data", "*.json"))
        return run_in_threads(lambda file: filter_by_type(load_json(file)), paths)

    def update_airports(self):
        """Synchronize the airport data with the database."""
        existing_airports = fetch_all_data("airports", "*")
        existing_by_source_id = {
            apt["source_id"]: deserialize_apt_json(apt) for apt in existing_airports
        }
        current_source_ids = {apt.source_id for apt in self.oap_airports}

        new_airports, changed_airports, removed_source_ids = self._categorize_airports(
            existing_by_source_id, current_source_ids
        )

        self._process_new_airports(new_airports)
        self._process_changed_airports(changed_airports)
        self._process_removed_airports(removed_source_ids)
        self._save_last_update()

    def _categorize_airports(self, existing_by_source_id, current_source_ids):
        """Categorize airports as new, changed, or removed."""
        logger.info("Determining changes...")
        new_airports, changed_airports = [], []
        removed_source_ids = list(set(existing_by_source_id) - current_source_ids)
        for apt in self.oap_airports:
            db_apt = existing_by_source_id.get(apt.source_id)
            if db_apt:
                if has_changed(apt, db_apt, APT_COMPARISON_FIELDS):
                    changed_airports.append(apt.to_db_dict())
            else:
                new_airports.append(apt.to_db_dict())

        return new_airports, changed_airports, removed_source_ids

    def _process_new_airports(self, new_airports: List[Dict]):
        if new_airports:
            logger.info("Inserting new airports...")
            for chunk in chunked(new_airports, INSERT_CHUNK_SIZE):
                db_client.table(APTS_TABLE).insert(chunk).execute()
            self.added_count += len(new_airports)

    def _process_changed_airports(self, changed_airports: List[Dict]):
        if changed_airports:
            logger.info("Updating changed airports...")
            for chunk in chunked(changed_airports, INSERT_CHUNK_SIZE):
                db_client.table(APTS_TABLE).upsert(chunk, on_conflict="source_id").execute()
            self.updated_count += len(changed_airports)

    def _process_removed_airports(self, removed_source_ids: List[str]):
        if removed_source_ids:
            logger.info("Removing airports not present in data...")
            for chunk in chunked(removed_source_ids, DELETE_CHUNK_SIZE):
                db_client.table(APTS_TABLE).delete().in_("source_id", chunk).execute()
            self.removed_count += len(removed_source_ids)

    def _save_last_update(self):
        now = datetime.now(timezone.utc).isoformat()
        details = {
            "added": self.added_count,
            "updated": self.updated_count,
            "removed": self.removed_count,
        }
        try:
            db_client.table(UPDATES_TABLE).insert(
                {
                    "category": self.CARTEGORY,
                    "details": details,
                }
            ).execute()

            logger.info(f"Updated last_update for category '{self.CARTEGORY} to {now}")
        except APIError as e:
            logger.error(
                f"Failed to update last_update for category '{self.CARTEGORY} in table '{UPDATES_TABLE}'. Error: {e}"
            )

    def report(self) -> dict:
        return {
            "added": self.added_count,
            "updated": self.updated_count,
            "removed": self.removed_count,
        }

    def run(self):
        self.download_airports()
        self.update_airports()
        if all([i > 0 for i in self.report().values()]):
            print("Airport DB Summary:")
            print(
                "\n".join(
                    f"{action.title()} airports: {count}"
                    for action, count in self.report().items()
                )
            )
        else:
            print("No changes.")


if __name__ == "__main__":
    updater = AirportUpdater()
    updater.run()
