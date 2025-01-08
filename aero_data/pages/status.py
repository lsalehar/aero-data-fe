from typing import List

import reflex as rx
from aero_data.components import header
from aero_data.components.container import main_container
from aero_data.state import DBUpdate


def print_report(item: List) -> rx.Component:
    return rx.text(f"{item[0]}: {item[1]}", size="1", color=rx.color("green", shade=11))


def update_button(text: str, **kwargs) -> rx.Component:
    default_props = {"color_scheme": "gray", "variant": "surface"}
    props = {**default_props, **kwargs}
    return rx.button(text, **props)


def update_button_state() -> rx.Component:
    return rx.match(
        DBUpdate.status,
        (DBUpdate.IDLE, update_button("Update", on_click=DBUpdate.update_airports)),
        (DBUpdate.RUNNING, update_button("Updating", loading=True)),
        (DBUpdate.ERROR, update_button("Retry", on_click=DBUpdate.update_airports)),
        update_button("Up to date", disabled=True),
    )  # type:ignore


@rx.page(route="/status", on_load=DBUpdate.determine_status)
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
                        rx.text(f"{DBUpdate.last_updated}", as_="span", size="2"),
                        spacing="1",
                        flex_grow="1",
                    ),
                    rx.cond(not rx.app.is_prod_mode(), update_button_state()),
                    align="center",
                ),
                rx.cond(
                    DBUpdate.status,
                    rx.box(
                        rx.text(
                            "Summary:",
                            size="2",
                            weight="medium",
                            color=rx.color("green", shade=11),
                        ),
                        rx.flex(
                            rx.foreach(DBUpdate.pretty_report, print_report),
                            justify="between",
                            width="100%",
                        ),
                        border_radius="0.25rem",
                        background_color=rx.color("green", shade=1),
                        padding="0.5rem",
                        margin_top="0.5rem",
                    ),
                ),
                width="100%",
            ),
            width="100%",
            spacing="1",
        ),
        rx.cond(
            DBUpdate.status == DBUpdate.ERROR,
            rx.callout(
                text=DBUpdate.error_msg,
                icon="triangle-alert",
                color_scheme="ruby",
                role="alert",
            ),
        ),
    )
