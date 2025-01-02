from typing import Optional

import reflex as rx


def switch(
    label: str,
    id_: str,
    default_checked: bool | rx.Var[bool] = False,
    tooltip_content: Optional[str] = None,
    on_change: rx.EventHandler | None = None,
) -> rx.Component:
    children = [
        rx.switch(
            name=id_,
            default_checked=default_checked,
            on_change=on_change,
            size="1",
            radius="small",
        ),
        rx.text(label, as_="label"),
    ]
    if tooltip_content:
        children.append(
            rx.tooltip(
                rx.icon("info", size=16, color=rx.color("gray", 10)), content=tooltip_content
            )
        )
    return rx.flex(*children, align="center", spacing="2")
