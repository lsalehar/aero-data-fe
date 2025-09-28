import reflex as rx  # noqa: D100

from aero_data.pages import (
    aip_to_openair_page,  # noqa: F401
    geojson_generator_page,  # noqa: F401
    index,  # noqa: F401
    openair_converter_page,  # noqa: F401
    status,  # noqa: F401
)

app = rx.App(
    theme=rx.theme(accent_color="blue", gray_color="slate", color_mode="inherit"),
)
