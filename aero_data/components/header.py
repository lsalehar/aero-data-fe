import reflex as rx

from aero_data.state import State


def header() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Aero Data", size="8", color=rx.color("blue", 11)),
            rx.hstack(
                rx.link(
                    "Home",
                    href="/",
                    underline="none",
                    color=rx.color("gray", 12),
                    weight=rx.cond(State.current_page == "/", "bold", "regular"),
                ),
                rx.link(
                    "Status",
                    href="/status",
                    underline="none",
                    color=rx.color("gray", 12),
                    weight=rx.cond(State.current_page == "/status", "bold", "regular"),
                ),
                spacing="4",
                align="start",
            ),
            width="100%",
            align="start",
        ),
        position="sticky",
        top="0",
        z_index="10",
    )
