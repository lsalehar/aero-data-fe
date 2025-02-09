import json
import logging
import os
from datetime import datetime, timedelta, timezone
from glob import glob
from typing import Dict, List

from decouple import config
from postgrest.exceptions import APIError

from aero_data import db_client
from aero_data.models import Airport
from aero_data.src.db import fetch_all_data, get_last_update
from aero_data.src.openaip import construct_airport_from_oap, filter_by_type
from aero_data.utils.file_handling import load_json, save_raw
from aero_data.utils.general import chunked, has_changed, run_in_threads
from aero_data.utils.google_cloud import GoogleCloudBucket

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

DATA_TABLE = "airports"
UPDATES_TABLE = "updates"
INSERT_CHUNK_SIZE = 10000
DELETE_CHUNK_SIZE = 500
OAP_PATH = "raw_data/oap"
STF_PATH = "raw_data/stf"


class Updater:
    _subclasses = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls not in Updater._subclasses:
            Updater._subclasses.append(cls)

    @classmethod
    def run(cls):
        for subclass in Updater._subclasses:
            print(f"Running subclass {subclass.__name__}")
            updater_instance = subclass()
            updater_instance.update()

    def update(self):
        raise NotImplementedError("Subclasses must implement the `update` method.")


class OAPUpdater(Updater):
    CARTEGORY = "airports"

    def __init__(self, last_update: datetime | None = get_last_update()):
        self.new_data = []
        self.added_count = 0
        self.updated_count = 0
        self.removed_count = 0
        self.last_update = last_update

    def download_data(self):
        """Download or load airport data and filter it."""

        # Fix Me: Maybe existing data does not exsist.
        if not self.last_update or datetime.now(timezone.utc) - self.last_update > timedelta(
            days=1
        ):
            oap_airports = self._download_new_data()
        else:
            oap_airports = self._load_existing_data()

        self.new_data = [construct_airport_from_oap(apt) for apt in oap_airports]

    def _download_new_data(self) -> List[Dict]:
        logger.info("Downloading new data from OpenAIP...")
        BUCKET = GoogleCloudBucket(config("GCLOUD_BUCKET_NAME"))  # type:ignore
        blobs = [blob for blob in BUCKET.blobs if blob.name.endswith("apt.json")]

        def download_and_process(blob):
            file = BUCKET.download_blob_into_memory(blob)
            save_raw(file, blob.name, OAP_PATH)
            return filter_by_type(json.loads(file.decode("utf-8")))

        return run_in_threads(download_and_process, blobs)

    def _load_existing_data(self) -> List[Dict]:
        logger.info("Loading existing data...")
        paths = glob(os.path.join(OAP_PATH, "*.json"))
        return run_in_threads(lambda file: filter_by_type(load_json(file)), paths)

    def update_data_in_db(self):
        """Synchronize the airport data with the database."""
        existing_airports = fetch_all_data("airports", "*")
        existing_by_source_id = {
            apt["source_id"]: Airport.deserialize_apt_json(apt) for apt in existing_airports
        }
        current_source_ids = {apt.source_id for apt in self.new_data}

        new_airports, changed_airports, removed_source_ids = self._categorize_airports(
            existing_by_source_id, current_source_ids
        )

        self._process_new_data(new_airports)
        self._process_changed_data(changed_airports)
        self._process_removed_data(removed_source_ids)
        self._save_last_update()

    def _categorize_airports(self, existing_by_source_id, current_source_ids):
        """Categorize airports as new, changed, or removed."""
        logger.info("Determining changes...")
        new_airports, changed_airports = [], []
        removed_source_ids = list(set(existing_by_source_id) - current_source_ids)
        for apt in self.new_data:
            db_apt = existing_by_source_id.get(apt.source_id)
            if db_apt:
                if has_changed(apt, db_apt, APT_COMPARISON_FIELDS):
                    changed_airports.append(apt.to_db_dict())
            else:
                new_airports.append(apt.to_db_dict())

        return new_airports, changed_airports, removed_source_ids

    def _process_new_data(self, new_airports: List[Dict]):
        if new_airports:
            logger.info("Inserting new airports...")
            for chunk in chunked(new_airports, INSERT_CHUNK_SIZE):
                db_client.table(DATA_TABLE).insert(chunk).execute()
            self.added_count += len(new_airports)

    def _process_changed_data(self, changed_airports: List[Dict]):
        if changed_airports:
            logger.info("Updating changed airports...")
            for chunk in chunked(changed_airports, INSERT_CHUNK_SIZE):
                db_client.table(DATA_TABLE).upsert(chunk, on_conflict="source_id").execute()
            self.updated_count += len(changed_airports)

    def _process_removed_data(self, removed_source_ids: List[str]):
        if removed_source_ids:
            logger.info("Removing airports not present in data...")
            for chunk in chunked(removed_source_ids, DELETE_CHUNK_SIZE):
                db_client.table(DATA_TABLE).delete().in_("source_id", chunk).execute()
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

    def update(self):
        self.download_data()
        self.update_data_in_db()
        if any([i > 0 for i in self.report().values()]):
            print("Airport DB Summary:")
            print(
                "\n".join(
                    f"{action.title()} airports: {count}"
                    for action, count in self.report().items()
                )
            )
        else:
            print("No changes.")


class STFUpdater(Updater):
    CARTEGORY = "outlandings"

    def _load_exisitng(self):
        logger.info("Loading exsiting Streckenflug data")
        paths = glob(os.path.join(STF_PATH, "*.json"))


if __name__ == "__main__":
    updater = OAPUpdater()
    updater.update()
