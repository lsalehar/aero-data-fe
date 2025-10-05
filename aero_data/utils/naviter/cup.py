import csv
import io
import logging
import os
from typing import Any, Iterable, List, Optional, Tuple

from charset_normalizer import from_bytes

from aero_data.utils.naviter.constants import CUP_FIELDS, CUP_FIELDS_MAPPING
from aero_data.utils.naviter.waypoint import CupWaypoint

logger = logging.getLogger()


class Waypoints(list):
    def append(self, item: Any):
        if not isinstance(item, CupWaypoint):
            raise TypeError(f"Item must be a CupWaypoint, got {type(item)}")
        super().append(item)

    def extend(self, iterable: Iterable):
        for item in iterable:
            if not isinstance(item, CupWaypoint):
                raise TypeError(f"All items must be CupWaypoint, got {type(item)}")
        super().extend(iterable)

    def insert(self, index, item):
        if not isinstance(item, CupWaypoint):
            raise TypeError(f"Item must be a CupWaypoint, got {type(item)}")
        super().insert(index, item)


class CupFile:
    """
    Representation of Cup File with support for waypoints. It stores and returns the tasks but
    there is no support for manipulating them.
    """

    def __init__(self, file_name: str | None = None):
        self.file_name: str | None = file_name
        self._waypoints: Waypoints = Waypoints()
        self._tasks: List[str] = []

    @property
    def waypoints(self) -> Waypoints:
        return self._waypoints

    def load(self, file_path: str) -> "CupFile":
        self.file_name = os.path.basename(file_path)
        try:
            self.file_name = os.path.basename(file_path)
            with open(file_path, "rb") as file_obj:
                content = file_obj.read()
            return self.loads(content)
        except IOError as e:
            logger.error(f"Error while reading file {file_path}: {e}")
            return self

    def loads(self, data: bytes | str):
        content: str
        if isinstance(data, bytes):
            results = from_bytes(data)
            chosen: str | None = None
            for result in results:
                enc = getattr(result, "encoding", None)
                if result.chaos == 0 and isinstance(enc, str) and enc.lower().startswith(("cp", "iso")):
                    chosen = str(result)
                    break
            content = chosen if chosen is not None else str(results.best())
        elif isinstance(data, str):
            # Treat input as already-decoded file content
            content = data
        else:
            raise TypeError(f"Unsupported data type for loads: {type(data)}")

        lines = content.splitlines()
        reader = csv.reader(lines, delimiter=",", quotechar='"')
        header_line = next(reader, None)
        if header_line is None:
            logger.warning("File is empty.")
            return self

        column_indices = self._find_column_indices(header_line)
        unique_wpt_ids = set()
        for line_nr, line in enumerate(reader):
            line_str = ",".join(line)
            if "--related tasks--" in line_str.lower():
                self._tasks = lines[line_nr + 2 :]
                break

            if line and not line[0].startswith("#"):
                self._add_wpt_if_unique(line, line_str, column_indices, unique_wpt_ids)

        return self

    def _find_column_indices(self, header_line):
        column_indeces = {}
        for i, column_name in enumerate(header_line):
            normalized_name = column_name.strip().lower()
            for field, possible_names in CUP_FIELDS_MAPPING.items():
                if normalized_name in possible_names:
                    column_indeces[field] = i
                    break

        return column_indeces

    def _add_wpt_if_unique(self, line, line_str, column_indices, unique_wpt_ids):
        if line_str not in unique_wpt_ids:
            waypoint = self._parse_waypoint_line(line, column_indices)
            unique_wpt_ids.add(line_str)
            self.waypoints.append(waypoint)

    def _parse_waypoint_line(self, line, column_indices):
        waypoint_data = {
            field: line[index].strip('"').strip() for field, index in column_indices.items()
        }
        return CupWaypoint(**waypoint_data)

    def _serialize(self):
        output = io.StringIO()
        # Write header
        output.write(",".join(CUP_FIELDS) + "\n")
        # Output waypoints
        for waypoint in self.waypoints:
            output.write(f"{waypoint}\n")
        # Write tasks seperator
        output.write("-----Related Tasks-----\n")
        # Output tasks
        if self._tasks:
            output.write("\n".join(self._tasks))

        return output.getvalue()

    def dump(self, file_path: str = ""):
        serialized = self._serialize()
        if not file_path:
            file_path = self.file_name if self.file_name else "unknown.cup"
        with open(file_path, "w") as f:
            f.write(serialized)
        return self

    def dumps(self):
        return self._serialize()

    def landables(self) -> list:
        return list(filter(lambda wpt: wpt.style in [2, 3, 4, 5], self.waypoints))

    def airports(self) -> list[CupWaypoint]:
        return list(filter(lambda wpt: wpt.style in [2, 4, 5], self.waypoints))

    def outlandings(self) -> list:
        return list(filter(lambda wpt: wpt.style == 3, self.waypoints))

    def get_bbox(self) -> Tuple[float, float, float, float] | None:
        if not self.waypoints:
            return None

        x, y = zip(*[(wpt.lat, wpt.lon) for wpt in self.waypoints])

        return (min(x), min(y), max(x), max(y))


def load(file_path: str) -> CupFile:
    return CupFile().load(file_path)


def loads(content: str | bytes) -> CupFile:
    return CupFile().loads(content)


def dump(cup_file: CupFile, file_path: Optional[str] = None) -> CupFile:
    if file_path:
        cup_file.dump(file_path)
    else:
        cup_file.dump()
    return cup_file


def dumps(cup_file: CupFile) -> str:
    return cup_file.dumps()
