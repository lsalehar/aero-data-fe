import reflex as rx

from aero_data.state import State


def footer() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                f"Page visits: {State.counter}",
                size="1",
                color_scheme="gray",
                text_align="left",
            ),
            rx.text(
                f"Files updated: {State.nr_updates}",
                size="1",
                color_scheme="gray",
                text_align="center",
            ),
            rx.hstack(
                rx.text("Version:", size="1", color_scheme="gray"),
                rx.link(
                    State.version,
                    href="https://github.com/lsalehar/aero-data-fe/releases",
                    underline="hover",
                    size="1",
                ),
                spacing="1",
            ),
            width="100%",
            align="center",
            justify="between",
        ),
        rx.text(
            "Privacy: Your file is processed transiently; no permanent storage.",
            size="1",
            color_scheme="gray",
            text_align="center",
        ),
        width="100%",
        align="stretch",
        justify="between",
    )
