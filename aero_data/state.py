import io
import os
import zipfile
from datetime import datetime
from typing import Optional

import reflex as rx

from aero_data.src.analytics import get_nr_updates, get_unique_visits, log_event
from aero_data.src.db import get_last_update_and_details
from aero_data.src.update_airports_in_cup import update_airports_in_cup
from aero_data.utils.naviter.cup import CupFile


class State(rx.State):
    @rx.var(cache=False)
    def current_page(self) -> str:
        return self.router.page.path

    @rx.event
    def log_page_visit(self):
        log_event(
            "page_visit",
            self.router.session.session_id,
            {"page_name": self.current_page},
        )

    def log_event(self, event: str, event_details: dict = {}):
        log_event(event, self.router.session.session_id, event_details)

    @rx.var(cache=True)
    def counter(self) -> int:
        return get_unique_visits()

    @rx.var(cache=True)
    def nr_updates(self) -> int:
        return get_nr_updates()

    @rx.var(cache=True)
    def version(self) -> str:
        config = rx.app.get_config()  # type:ignore
        return config.version  # type: ignore


class UpdateCupFile(State):
    PRE_UPDATE = "pre-update"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"

    stage: str = PRE_UPDATE
    file_name: str = ""
    error_message: str = ""
    update_locations: bool = True
    add_missing: bool = True
    delete_closed: bool = False
    _zip_file: Optional[bytes] = None

    @rx.event
    def reset_state(self, upload_id: str):
        """
        Reset the state variables to their initial values.
        """
        self.stage = self.PRE_UPDATE
        self.file_name = ""
        yield rx.clear_selected_files(upload_id)

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        try:
            self.stage = self.RUNNING
            yield

            for file in files:
                data = await file.read()
                file_name = file.filename or ""
                self.file_name = os.path.basename(file_name)

            if data:
                self.log_event("upload", {"file_name": file.filename, "file_size": file.size})

            updated_file, report = update_airports_in_cup(
                data,
                self.file_name,
                fix_location=self.update_locations,
                delete_closed=self.delete_closed,
                add_new=self.add_missing,
            )

            updated_file_name = self.file_name.replace(".cup", "-updated.cup")
            self.log_event("cup_updated", {"file_name": updated_file_name})

            self._zip_file = self.create_zip(updated_file, updated_file_name, report)

            self.stage = self.DONE
            yield
        except Exception as e:
            self.stage = self.ERROR
            self.error_message = str(e)
            self.log_event("upload_error", {"error": self.error_message})
            yield

    def create_zip(self, updated_file: CupFile, updated_file_name: str, report: str) -> bytes:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(updated_file_name, updated_file.dumps())
            zip_file.writestr("update_report.txt", report)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @rx.event
    def download_zip(self):
        if not self._zip_file:
            raise ValueError("No ZIP file avaialable for download")

        updated_name = f"{self.file_name.replace(".cup", "")}_updated.zip"

        self.log_event(
            "download_update_package",
            {"file_name": updated_name, "file_size": len(self._zip_file)},
        )

        yield rx.download(filename=updated_name, data=self._zip_file)


class DBStatus(State):
    loading: bool = True
    report: dict[str, int] = {}
    _last_updated: Optional[datetime] = None

    @rx.var(cache=True)
    def last_updated(self) -> str:
        if self._last_updated:
            return self._last_updated.strftime("%d.%m.%Y @ %H:%M:%S %Z")
        return ""

    @rx.var(cache=True)
    def pretty_report(self) -> dict:
        if not self.report:
            return {}
        return {key.title(): value for key, value in self.report.items()}

    @rx.event
    async def determine_status(self):
        self.loading = True
        yield

        self.log_page_visit()
        data = get_last_update_and_details() or {}

        self.report = data.get("details", {})
        if data.get("timestamp"):
            self._last_updated = datetime.fromisoformat(data["timestamp"])
        else:
            self._last_updated = None

        self.loading = False
        yield
