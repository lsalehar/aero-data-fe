import os
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from more_itertools import chunked

from aero_data.models import Airport
from aero_data.src.db import get_nearest_airport_bulk
from aero_data.utils.naviter import CupFile, cup
from aero_data.utils.naviter.waypoint import CupWaypoint
from aero_data.utils.openaip.constants import AirportType


def generate_report(file_name: str | None, search_r: int, counts: dict, data: dict) -> str:
    report = f"""
############################################################
Report for: {file_name or "Unknown File Name"}
Updated on: {datetime.now(timezone.utc).isoformat(timespec="minutes")}
############################################################

# General
Before update:
{counts['total_wpts_before']} total waypoints
{counts['total_apts_before']} airports of which:
    - {counts['updated']} were updated,
    - {counts['removed']} were removed,
    - {counts['not_found']} where no update was found.

After update:
{counts['total_wpts_after']} total waypoints
{counts['total_apts_after']} airports

"""

    report += "# List of updated airports:\n"
    for item in data["updated"]:
        report += f"Old: {item[0]}\n"
        report += f"New: {item[1]}\n"
        report += f"Dst: {float(item[2]):.0f} m\n\n"

    if data["removed"]:
        report += "# List of removed airports:\n"
        for item in data["removed"]:
            report += (
                f"Removed {item[0].name}, {item[0].lat} {item[0].lon} because it is closed\n"
            )
            report += f"Dst: {float(item[2]):.0f} m\n\n"

    if data["not_fonud"]:
        report += "\n# List of not updated airports:\n"
        for item in data["not_found"]:
            report += f"{item}"

    return report


class AirportDistance(Airport):
    def __init__(self, distance: Optional[float] = None, **kwargs):
        super().__init__(**kwargs)
        self.distance = distance


def parse_annotated_airports(results: list[dict]) -> dict[int, Optional[AirportDistance]]:
    """
    Parse results from bulk query into AirportDistance objects.

    Args:
        results (list[dict]): Results from the `get_nearby_airports_bulk` RPC call.

    Returns:
        dict[int, Optional[AirportDistance]]: Mapping of point indices to AirportDistance objects.
    """
    annotated_airports = {}

    for record in results:
        point_index = record["point_index"]

        if record["id"] is None:
            annotated_airports[point_index] = None
            continue

        airport_data = Airport.deserialize_apt_json(
            {k: v for k, v in record.items() if k != "point_index"}, as_dict=True
        )
        annotated_airports[point_index] = AirportDistance(**airport_data)  # type:ignore

    return annotated_airports


def update_cup_waypoint(waypoint1: CupWaypoint, waypoint2: CupWaypoint, attrs: tuple | list):
    """
    Update attributes of a CUP waypoint based on another waypoint.

    Args:
        waypoint1 (CupWaypoint): The waypoint to update.
        waypoint2 (CupWaypoint): The waypoint providing new data.
        attrs (tuple | list): List of attributes to update.
    """
    for attr in attrs:
        new_value = getattr(waypoint2, attr)
        if new_value:
            setattr(waypoint1, attr, new_value)


# FIXME: There are not_updated and not_found airports, print those to the report and also check
# what is the difference.
def update_airports_in_cup(
    file: bytes,
    file_name: str,
    search_r: int = 5000,
    update_r: int = 2000,
    fix_location: bool = True,
    delete_closed: bool = False,
):
    """
    Update airports in a CUP file using bulk queries to the database.

    Args:
        file (bytes): The CUP file data.
        file_name (str): The name of the CUP file.
        db_client: Supabase client for database interaction.
        search_r (int): Search radius in meters.
        update_r (int): Update radius in meters.
        fix_location (bool): Whether to fix airport locations.
        delete_closed (bool): Whether to delete closed airports.

    Returns:
        tuple: Updated CUP file and a report.
    """

    # Setup
    data_report = defaultdict(list)
    counts = defaultdict(int)
    tresholds = [
        (dist, f"distance_lte_{dist}m") for dist in range(500, (update_r // 500) * 500, 500)
    ]

    fields = (
        (
            "lat",
            "lon",
            "elev",
            "style",
            "rwdir",
            "rwlen",
            "rwwidth",
            "freq",
        )
        if fix_location
        else (
            "elev",
            "style",
            "rwdir",
            "rwlen",
            "rwwidth",
            "freq",
        )
    )
    chunk_size = 500

    # Load file
    cup_file = CupFile(file_name=file_name)
    cup_file.loads(file)

    airports_in_cup = cup_file.airports()
    counts["total_wpts_before"] = len(cup_file.waypoints)
    counts["total_apts_before"] = len(airports_in_cup)

    # Prepare points for bulk queries
    points = [apt.get_point() for apt in airports_in_cup]

    for point_chunk, apt_chunk in zip(
        chunked(points, chunk_size), chunked(airports_in_cup, chunk_size)
    ):
        result = get_nearest_airport_bulk(point_chunk, search_r)  # type:ignore
        airports_from_db = parse_annotated_airports(result)  # type:ignore

        for point_index, apt_in_cup in enumerate(apt_chunk):
            closest_apt = airports_from_db.get(point_index + 1)

            if not closest_apt or closest_apt.distance is None:
                data_report["not_found"].append(apt_in_cup)
                continue

            if closest_apt.distance <= update_r:
                if not closest_apt.apt_type == AirportType.CLOSED:
                    data_report["updated"].append(
                        (deepcopy(apt_in_cup), apt_in_cup, closest_apt.distance)
                    )
                    update_cup_waypoint(apt_in_cup, closest_apt.to_cup(), fields)
                    for threshold, key in tresholds:
                        if closest_apt.distance <= threshold:
                            counts[key] += 1
                            break
                else:
                    if delete_closed:
                        cup_file.waypoints.remove(apt_in_cup)
                        data_report["removed"].append(
                            (deepcopy(apt_in_cup), closest_apt.to_cup(), closest_apt.distance)
                        )

            else:
                data_report["not_updated"].append(
                    (deepcopy(apt_in_cup), closest_apt.to_cup(), closest_apt.distance)
                )

    counts["updated"] = len(data_report["updated"])
    counts["removed"] = len(data_report["removed"])
    counts["not_found"] = len(data_report["not_found"])
    counts["total_wpts_after"] = len(cup_file.waypoints)
    counts["total_apts_after"] = len(cup_file.airports())

    report = generate_report(cup_file.file_name, search_r, counts, data_report)

    return cup_file, report


if __name__ == "__main__":
    file_path = "test_files/kdf20101.cup"
    fp, fn = os.path.split(file_path)
    fn = fn.removesuffix(".cup")
    print(os.getcwd())
    with open(file_path, "rb") as f:
        cup_file = f.read()
    cup_file, report = update_airports_in_cup(cup_file, fn, delete_closed=True)
    cup.dump(cup_file, f"uploaded_files/{fn}_updated.cup")
    with open(f"uploaded_files/{fn}_report.txt", "w") as f:
        f.write(report)
