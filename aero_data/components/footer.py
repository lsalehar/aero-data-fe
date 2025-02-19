import reflex as rx

from aero_data.state import State


def footer() -> rx.Component:
    return rx.hstack(
        rx.text(f"Page visits: {State.counter}", size="1", color_scheme="gray"),
        rx.text(f"Version: {State.version}", size="1", color_scheme="gray"),
        justify="between",
        width="100%",
    )
