import reflex as rx
from aero_data.state import State


def header() -> rx.Component:
    return rx.vstack(
        rx.heading("Aero Data", size="9", color=rx.color("blue", 11)),
        rx.text(
            "Helping you with your aeronautical data needs since 2025.",
            font_family="monospace",
            size="1",
            color=rx.color("gray", 11),
        ),
        rx.cond(
            State.current_page != "/",
            rx.link("Home", href="/"),
            rx.link("Status", href="/status"),
        ),
        spacing="1",
    )
