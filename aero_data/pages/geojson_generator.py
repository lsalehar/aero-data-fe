import reflex as rx

from aero_data.components import header
from aero_data.state import GeoState


@rx.page(route="/geojson")
def geojson_generator_page() -> rx.Component:
    """
    Reflex page for generating GeoJOSN polygons from coordinate input.
    """
    return rx.container(
        rx.vstack(
            header(),
            # --- Existing Polygon Generator Section ---
            rx.heading("GeoJSON Polygon Generator", size="7"),
            rx.input(
                placeholder="Enter polygon name",
                value=GeoState.name,
                on_change=GeoState.set_name,  # type: ignore
                width="100%",
            ),
            rx.text_area(
                placeholder=(
                    "Paste coordinates. Supported: DP (46:39:59 N 016:02:10 E), "
                    "AIP (455404.3N 0153113.7E), eAPI (46 10 29 N 013 39 58 E)"
                ),
                value=GeoState.raw_input,
                on_change=GeoState.set_raw_input,  # type: ignore
                rows="10",
                width="100%",
            ),
            rx.button("Generate GeoJSON", on_click=GeoState.generate_geojson),
            rx.cond(GeoState.error != "", rx.text(GeoState.error, color="red.500")),
            rx.cond(
                GeoState.geojson_result != "",
                rx.text_area(
                    value=GeoState.geojson_result, read_only=True, rows="20", width="100%"
                ),
            ),
            rx.divider(),
            rx.heading("AIP Coordinate Converter", size="6"),
            rx.input(
                placeholder="Paste AIP coordinates (one per line, e.g. 455404.3N 0153113.7E)",
                value=GeoState.aip_input,
                on_change=GeoState.set_aip_input,
                width="100%",
            ),
            rx.hstack(
                rx.button("Convert single point", on_click=GeoState.convert_aip),
                rx.button("Convert list to GeoJSON", on_click=GeoState.convert_aip_list),
            ),
            rx.cond(
                GeoState.aip_result != "",
                rx.code(GeoState.aip_result),
            ),
            rx.cond(
                GeoState.aip_geojson_list != "",
                rx.text_area(
                    value=GeoState.aip_geojson_list,
                    read_only=True,
                    rows="10",
                    width="100%",
                    style={"fontFamily": "monospace"},
                ),
            ),
            rx.cond(
                GeoState.error != "",
                rx.text(GeoState.error, color="red.500"),
            ),
            rx.heading("ICAO Compact Coordinates to GeoJSON Polygon", size="6"),
            rx.text_area(
                value=GeoState.icao_input,
                on_change=GeoState.set_icao_input,
                rows="12",
                width="100%",
                placeholder=(
                    "Paste ICAO compact coordinates here (e.g. 461010N 0144103E -), "
                    "one per line or all at once."
                ),
                style={"fontFamily": "monospace"},
            ),
            rx.button(
                "Convert to GeoJSON Polygon",
                on_click=GeoState.convert_icao_to_geojson,
                width="100%",
            ),
            rx.cond(
                GeoState.icao_geojson != "",
                rx.text_area(
                    value=GeoState.icao_geojson,
                    read_only=True,
                    rows="12",
                    width="100%",
                    style={"fontFamily": "monospace"},
                ),
            ),
            rx.cond(
                GeoState.error != "",
                rx.text(GeoState.error, color="red.500"),
            ),
            spacing="4",
            width="100%",
        ),
        padding="4",
        max_width="800px",
        margin="auto",
    )
