from typing import List

import reflex as rx

from aero_data.components import footer, header
from aero_data.components.container import main_container
from aero_data.state import DBStatus


def print_report(item: List) -> rx.Component:
    return rx.text(
        f"{item[0]}:", rx.text(f"{item[1]}", color=rx.color("gray", 12), size="2"), size="1"
    )


@rx.page(route="/status", on_load=DBStatus.determine_status)
def status() -> rx.Component:
    return main_container(
        header(),
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Airports DB", size="5"),
                        rx.text(
                            "Data from: ",
                            rx.link(
                                "OpenAIP",
                                href="https://www.openaip.net",
                            ),
                            size="1",
                            color_scheme="gray",
                        ),
                        width="100%",
                        align="baseline",
                        justify="between",
                    ),
                    rx.text(
                        "Last updated:",
                        size="1",
                        color=rx.color("gray", 11),
                        trim="end",
                    ),
                    rx.cond(
                        DBStatus.loading,
                        rx.skeleton(width="40%", height="1.2em"),
                        rx.text(f"{DBStatus.last_updated}", as_="span", size="2"),
                    ),
                    rx.cond(
                        DBStatus.loading,
                        rx.hstack(
                            rx.skeleton(width="33%", height="2.4em"),
                            rx.skeleton(width="33%", height="2.4em"),
                            rx.skeleton(width="33%", height="2.4em"),
                            width="100%",
                        ),
                        rx.flex(
                            rx.foreach(DBStatus.pretty_report, print_report),
                            color=rx.color("gray", 11),
                            justify="between",
                            width="100%",
                        ),
                    ),
                    spacing="1",
                    flex_grow="1",
                ),
                width="100%",
                align="center",
            ),
            width="100%",
            spacing="1",
        ),
        footer(),
    )
