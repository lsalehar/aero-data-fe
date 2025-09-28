import reflex as rx

from aero_data.components import header
from aero_data.state import OpenAirConverterState


@rx.page(route="/openair-converter")
def openair_converter_page() -> rx.Component:
    """
    Page for converting between OpenAir and GeoJSON formats, with upload/download support.
    """
    return rx.container(
        rx.vstack(
            header(),
            rx.heading("OpenAir & GeoJSON Converter", size="7"),
            rx.hstack(
                # OpenAir section
                rx.vstack(
                    rx.text("OpenAir format", weight="bold"),
                    rx.text_area(
                        value=OpenAirConverterState.openair_input,
                        on_change=OpenAirConverterState.set_openair_input,  # type: ignore
                        rows="20",
                        width="100%",
                        placeholder="Paste OpenAir text here...",
                        style={"fontFamily": "monospace"},
                    ),
                    rx.button(
                        "Convert to GeoJSON",
                        on_click=OpenAirConverterState.convert_openair_to_geojson,
                        width="100%",
                    ),
                    rx.cond(
                        OpenAirConverterState.openair_error != "",
                        rx.text(OpenAirConverterState.openair_error, color="red.500"),
                    ),
                    width="48%",
                ),
                # GeoJSON section
                rx.vstack(
                    rx.text("GeoJSON format", weight="bold"),
                    rx.text_area(
                        value=OpenAirConverterState.geojson_input,
                        on_change=OpenAirConverterState.set_geojson_input,  # type: ignore
                        rows="20",
                        width="100%",
                        placeholder="Paste GeoJSON here...",
                        style={"fontFamily": "monospace"},
                    ),
                    rx.button(
                        "Convert to OpenAir",
                        on_click=OpenAirConverterState.convert_geojson_to_openair,
                        width="100%",
                    ),
                    rx.cond(
                        OpenAirConverterState.geojson_error != "",
                        rx.text(OpenAirConverterState.geojson_error, color="red.500"),
                    ),
                    width="48%",
                ),
                spacing="4",
                width="100%",
            ),
            spacing="4",
        ),
        padding="4",
        max_width="900px",
        margin="auto",
    )
