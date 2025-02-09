from typing import List

import reflex as rx
from aero_data.components import header
from aero_data.components.container import main_container
from aero_data.state import DBStatus


def print_report(item: List) -> rx.Component:
    return rx.text(f"{item[0]}: {item[1]}", size="1", color=rx.color("green", shade=11))


@rx.page(route="/status", on_load=DBStatus.determine_status)
def status() -> rx.Component:
    return main_container(
        header(),
        rx.vstack(
            rx.card(
                rx.hstack(
                    rx.vstack(
                        rx.heading("Airports DB", size="5"),
                        rx.text(
                            "Last updated:",
                            size="2",
                            color=rx.color("gray", 11),
                            trim="end",
                        ),
                        rx.text(f"{DBStatus.last_updated}", as_="span", size="2"),
                        spacing="1",
                        flex_grow="1",
                    ),
                    align="center",
                ),
                rx.box(
                    rx.text(
                        "Summary:",
                        size="2",
                        weight="medium",
                        color=rx.color("green", shade=11),
                    ),
                    rx.flex(
                        rx.foreach(DBStatus.pretty_report, print_report),
                        justify="between",
                        width="100%",
                    ),
                    border_radius="0.25rem",
                    background_color=rx.color("green", shade=1),
                    padding="0.5rem",
                    margin_top="0.5rem",
                ),
                width="100%",
            ),
            width="100%",
            spacing="1",
        ),
    )
