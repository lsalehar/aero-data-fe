import json
from typing import Any


def fix_geojson_polygons(geojson_str: str) -> str:
    """
    Loads a GeoJSON string, closes all Polygon/MultiPolygon rings if needed, and returns the fixed string.
    """
    with open(geojson_str, "r") as fp:
        data = json.load(fp)

    def close_ring(ring: list[list[float]]) -> list[list[float]]:
        if ring and ring[0] != ring[-1]:
            ring.append(ring[0])
        return ring

    def fix_geometry(geom: dict[str, Any]) -> None:
        if geom["type"] == "Polygon":
            geom["coordinates"] = [close_ring(ring) for ring in geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            geom["coordinates"] = [
                [close_ring(ring) for ring in polygon] for polygon in geom["coordinates"]
            ]
        # Optionally recurse for GeometryCollection

    if data.get("type") == "FeatureCollection":
        for feature in data["features"]:
            fix_geometry(feature["geometry"])
    elif data.get("type") in ("Polygon", "MultiPolygon"):
        fix_geometry(data)
    else:
        raise ValueError("GeoJSON must be a FeatureCollection or (Multi)Polygon.")

    return data


from aero_data.utils.naviter import dump, load


def fix_cup(file: str):
    cup = load(file)

    dump(cup, file)


if __name__ == "__main__":
    file = "wp-aac2025-3.cup"
    fix_cup(file)
