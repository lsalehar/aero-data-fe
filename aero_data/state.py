import io
import os
import zipfile
from datetime import datetime

import reflex as rx

from aero_data.src.analytics import get_nr_updates, get_unique_visits, log_event
from aero_data.src.db import get_last_update_and_details
from aero_data.src.update_airports_in_cup import update_airports_in_cup
from aero_data.utils.naviter.cup import CupFile
from aero_data.utils.naviter.openair import geojson_to_openair, openair_to_geojson
from aero_data.utils.units import (
    batch_compact_to_openair,
    extract_all_supported_coords,
    icao_coords_to_geojson_polygon,
    parse_aip_point,
    parse_line_to_lon_lat_any,
)


class State(rx.State):
    @rx.var(cache=False)
    def current_page(self) -> str:
        return self.router.url.path

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
    _zip_file: bytes | None = None

    def set_update_locations(self, value: bool) -> None:
        """Set the update_locations flag.

        Args:
            value (bool): If True, update airport locations during the update process.

        """
        self.update_locations = value

    def set_add_missing(self, value: bool) -> None:
        """Set the add_missing flag.

        Args:
            value (bool): If True, add missing airports during the update process.

        """
        self.add_missing = value

    def set_delete_closed(self, value: bool) -> None:
        """Set the delete_closed flag.

        Args:
            value (bool): If True, delete closed airports during the update process.

        """
        self.delete_closed = value

    @rx.event
    def reset_state(self, upload_id: str):
        """Reset the state variables to their initial values."""
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

        updated_name = f"{self.file_name.replace('.cup', '')}_updated.zip"

        self.log_event(
            "download_update_package",
            {"file_name": updated_name, "file_size": len(self._zip_file)},
        )

        yield rx.download(filename=updated_name, data=self._zip_file)


class DBStatus(State):
    loading: bool = True
    report: dict[str, int] = {}
    _last_updated: datetime | None = None

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


class GeoState(rx.State):
    name: str = ""
    raw_input: str = ""
    geojson_result: str = ""
    error: str = ""
    aip_input: str = ""
    aip_result: str = ""
    aip_geojson_list: str = ""
    icao_input: str = ""
    icao_geojson: str = ""

    def set_name(self, value: str):
        self.name = value

    def set_raw_input(self, value: str):
        self.raw_input = value

    def set_aip_input(self, value: str):
        self.aip_input = value

    def set_icao_input(self, value: str):
        self.icao_input = value

    @rx.event
    def generate_geojson(self) -> None:
        """Generate GeoJSON from polygon name and various coordinate formats."""
        try:
            lines = [l for l in self.raw_input.strip().split("\n") if l.strip()]
            coords = [parse_line_to_lon_lat_any(line) for line in lines]
            if coords[0] != coords[-1]:
                coords.append(coords[0])  # close the polygon
            feature = {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Polygon", "coordinates": [coords]},
            }
            if self.name:
                feature.update(properties={"name": self.name})
            import json

            self.geojson_result = json.dumps(feature, indent=2)
            self.error = ""
        except Exception as e:
            self.geojson_result = ""
            self.error = str(e)

    @rx.event
    def convert_aip(self) -> None:
        """Convert AIP string to GeoJSON coordinate format."""
        try:
            lat, lon = parse_aip_point(self.aip_input.strip())
            # GeoJSON expects [lon, lat]
            self.aip_result = f"[{lon:.7f}, {lat:.7f}]"
            self.error = ""
        except Exception as e:
            self.aip_result = ""
            self.error = str(e)

    @rx.event
    def convert_aip_list(self) -> None:
        """Convert multiple AIP/eAPI/ICAO points in any mix to a GeoJSON coordinate list."""
        try:
            coords = extract_all_supported_coords(self.aip_input)
            if not coords:
                raise ValueError("No valid coordinates found in input.")
            import json

            self.aip_geojson_list = json.dumps(coords, indent=2)
            self.error = ""
        except Exception as e:
            self.aip_geojson_list = ""
            self.error = str(e)

    @rx.event
    def convert_icao_to_geojson(self) -> None:
        """Convert ICAO compact format coordinates to GeoJSON Polygon."""
        try:
            self.icao_geojson = icao_coords_to_geojson_polygon(self.icao_input)
            self.error = ""
        except Exception as e:
            self.icao_geojson = ""
            self.error = str(e)


class OpenAirConverterState(rx.State):
    """State for the OpenAir <-> GeoJSON converter."""

    openair_input: str = ""
    geojson_input: str = ""
    openair_error: str = ""
    geojson_error: str = ""

    def set_openair_input(self, value: str):
        self.openair_input = value

    def set_geojson_input(self, value: str):
        self.geojson_input = value

    @rx.event
    def convert_openair_to_geojson(self) -> None:
        """Convert OpenAir text to GeoJSON."""
        try:
            self.geojson_input = openair_to_geojson(self.openair_input)
            self.geojson_error = ""
        except Exception as e:
            self.geojson_error = f"Conversion error: {e}"

    @rx.event
    def convert_geojson_to_openair(self) -> None:
        """Convert GeoJSON text to OpenAir."""
        try:
            self.openair_input = geojson_to_openair(self.geojson_input)
            self.openair_error = ""
        except Exception as e:
            self.openair_error = f"Conversion error: {e}"


class CompactToOpenAirState(rx.State):
    input_text: str = ""
    output_text: str = ""
    error: str = ""

    def set_input_text(self, value: str):
        self.input_text = value

    @rx.event
    def convert(self) -> None:
        try:
            result_lines = batch_compact_to_openair(self.input_text)
            if not result_lines:
                raise ValueError("No valid eAIP/AIP coordinates found.")
            self.output_text = "\n".join(result_lines)
            self.error = ""
        except Exception as e:
            self.output_text = ""
            self.error = str(e)
