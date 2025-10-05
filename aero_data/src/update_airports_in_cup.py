import os
from collections import defaultdict
from copy import deepcopy
from datetime import UTC, datetime

from more_itertools import chunked
from shapely import MultiPoint

from aero_data.models import Airport
from aero_data.src.db import get_apts_in_bbox, get_nearest_airport_bulk
from aero_data.utils.naviter import CupFile, cup
from aero_data.utils.naviter.waypoint import CupWaypoint
from aero_data.utils.openaip.constants import AirportType


def generate_report(
    file_name: str | None, counts: dict, data: dict, search_r: int, update_r: int
) -> str:
    report = f"""
############################################################
Report for: {file_name or "Unknown File Name"}
Updated on: {datetime.now(UTC).isoformat(timespec="minutes")}
############################################################

# General
Before the update the file had:
{counts["total_wpts_before"]} total waypoints
{counts["total_apts_before"]} airports

We search for candidates in the OpenAip DB with a radius of {search_r}m around the point of the 
airport stored in the CUP file. The airport is updated if the distance between the point of the 
airport and the found airport in the OpenAIP is less than the update radius of: {update_r}m

After update the file has:
{counts["total_wpts_after"]} total waypoints
{counts["total_apts_after"]} airports

{counts["updated"]} Airports were updated,
{counts["added"]} were added,
{counts["deleted"]} were deleted,
{counts["not_found"]} were not found in the OpenAIP DB and,
{counts["not_updated"]} were already up to date.

"""

    if data["updated"]:
        report += "# List of updated airports:\n"
        for item in data["updated"]:
            report += f"Old: {item[0]}\n"
            report += f"New: {item[1]}\n"
            report += f"Dst: {float(item[2]):.0f}m\n\n"

    if data["added"]:
        report += "# List of added airports:\n"
        for item in data["added"]:
            report += f"{item.name}: {item.lat:0.6}, {item.lon:0.6}\n"
        report += "\n"

    if data["deleted"]:
        report += "# List of deleted airports:\n"
        for item in data["deleted"]:
            report += f"{item[0].name}: {item[0].lat:0.6}, {item[0].lon:0.6} Closed. Dst: {float(item[2]):.0f}m\n"
        report += "\n"

    if data["not_updated"]:
        report += "\n# List of airports that were not updated:\n"
        for item in data["not_updated"]:
            report += f"Apt in CUP:\t{item[0]}\n"
            report += f"Candidate:\t{item[1]}\n"
            report += f"Dst:\t\t{float(item[2]):.0f}m > {update_r}\n\n"

    if data["not_found"]:
        report += "\n# List of airports that were not found in the DB:\n"
        for item in data["not_found"]:
            report += f"{item.name}: {item.lat:0.6}, {item.lon:0.6}\n"

    return report


class AirportDistance(Airport):
    def __init__(self, distance: float | None = None, **kwargs):
        super().__init__(**kwargs)
        self.distance = distance


def parse_annotated_airports(results: list[dict]) -> dict[int, AirportDistance | None]:
    """
    Parse results from bulk query into AirportDistance objects.

    Args:
        results (list[dict]): Results from the `get_nearby_airports_bulk` RPC call.

    Returns:
        dict[int, Optional[AirportDistance]]: Mapping of point indices to AirportDistance objects.
    """
    return {
        record["point_index"]: (
            AirportDistance(
                **Airport.deserialize_apt_json_to_dict(
                    {k: v for k, v in record.items() if k != "point_index"}
                )
            )
            if record["id"] is not None
            else None
        )
        for record in results
    }


def update_cup_waypoint(
    waypoint1: CupWaypoint, waypoint2: CupWaypoint, attrs: tuple | list
):
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


def update_airports_in_cup(
    file: bytes,
    file_name: str,
    search_r: int = 5000,
    update_r: int = 2000,
    fix_location: bool = True,
    delete_closed: bool = False,
    add_new: bool = False,
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
        tuple: (CupFile, report_text, counts_dict, data_report_dict)
    """

    # Setup
    data_report = defaultdict(list)
    counts = defaultdict(int)
    tresholds = [
        (dist, f"distance_lte_{dist}m")
        for dist in range(500, (update_r // 500) * 500, 500)
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
    # Prepare a list of ids that we've seen in the file
    seen_ids = []

    for point_chunk, apt_chunk in zip(
        chunked(points, chunk_size), chunked(airports_in_cup, chunk_size), strict=False
    ):
        result = get_nearest_airport_bulk(point_chunk, search_r)  # type:ignore
        airports_from_db = parse_annotated_airports(result)  # type:ignore

        for point_index, apt_in_cup in enumerate(apt_chunk):
            closest_apt = airports_from_db.get(point_index + 1)

            if not closest_apt or closest_apt.distance is None:
                data_report["not_found"].append(apt_in_cup)
                continue

            if closest_apt.distance <= update_r:
                seen_ids.append(closest_apt.source_id)
                if not closest_apt.apt_type == AirportType.CLOSED:
                    data_report["updated"].append(
                        (deepcopy(apt_in_cup), apt_in_cup, closest_apt.distance)
                    )
                    update_cup_waypoint(apt_in_cup, closest_apt.to_cup(), fields)
                    for threshold, key in tresholds:
                        if closest_apt.distance <= threshold:
                            counts[key] += 1
                            break
                elif delete_closed:
                    cup_file.waypoints.remove(apt_in_cup)
                    data_report["deleted"].append(
                        (
                            deepcopy(apt_in_cup),
                            closest_apt.to_cup(),
                            closest_apt.distance,
                        )
                    )

            else:
                data_report["not_updated"].append(
                    (deepcopy(apt_in_cup), closest_apt.to_cup(), closest_apt.distance)
                )

        if add_new:
            new_apts = get_apts_in_bbox(
                MultiPoint(point_chunk).bounds,
                exclude_source_ids=seen_ids,
                exclude_apt_types=[
                    AirportType.AIRPORT_WATER,
                    AirportType.CLOSED,
                    AirportType.HELIPORT_CIVIL,
                    AirportType.HELIPORT_MIL,
                    AirportType.UNKNOWN,
                ],
            )
            if new_apts:
                for apt in new_apts:
                    apt_obj = Airport.deserialize_apt_json(apt)
                    cup_file.waypoints.append(apt_obj.to_cup())
                    seen_ids.append(apt_obj.source_id)  # type: ignore
                    data_report["added"].append(apt_obj.to_cup())

    counts["updated"] = len(data_report["updated"])
    counts["added"] = len(data_report["added"])
    counts["deleted"] = len(data_report["deleted"])
    counts["not_found"] = len(data_report["not_found"])
    counts["not_updated"] = len(data_report["not_updated"])
    counts["total_wpts_after"] = len(cup_file.waypoints)
    counts["total_apts_after"] = len(cup_file.airports())

    report = generate_report(
        cup_file.file_name, counts, data_report, search_r, update_r
    )

    return cup_file, report, dict(counts), {k: list(v) for k, v in data_report.items()}


if __name__ == "__main__":
    file_path = "raw_data/test_cup_files/kdf20101.cup"
    fp, fn = os.path.split(file_path)
    fn = fn.removesuffix(".cup")
    print(os.getcwd())
    with open(file_path, "rb") as f:
        cup_file = f.read()
    cup_file, report = update_airports_in_cup(
        cup_file, fn, delete_closed=True, add_new=True
    )
    cup.dump(cup_file, f"{fp}/{fn}_updated.cup")
    with open(f"{fp}/{fn}_report.txt", "w") as f:
        f.write(report)
