import reflex as rx

from aero_data.components import header
from aero_data.state import CompactToOpenAirState


@rx.page(route="/aip-to-openair")
def aip_to_openair_page() -> rx.Component:
    return rx.container(
        rx.vstack(
            header(),
            rx.heading("AIP/eAIP to OpenAir DP Converter", size="7"),
            rx.text("Paste one or more AIP compact coordinates (e.g. 455210N 0135035E) below:"),
            rx.text_area(
                value=CompactToOpenAirState.input_text,
                on_change=CompactToOpenAirState.set_input_text,
                rows="10",
                width="100%",
                placeholder="One coordinate per line...",
                style={"fontFamily": "monospace"},
            ),
            rx.button(
                "Convert to OpenAir DP",
                on_click=CompactToOpenAirState.convert,
                width="100%",
            ),
            rx.cond(
                CompactToOpenAirState.output_text != "",
                rx.text_area(
                    value=CompactToOpenAirState.output_text,
                    read_only=True,
                    rows="10",
                    width="100%",
                    style={"fontFamily": "monospace"},
                ),
            ),
            rx.cond(
                CompactToOpenAirState.error != "",
                rx.text(CompactToOpenAirState.error, color="red.500"),
            ),
            spacing="4",
        ),
        padding="4",
        max_width="600px",
        margin="auto",
    )
