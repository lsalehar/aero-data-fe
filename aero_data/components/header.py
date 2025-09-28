import reflex as rx

from aero_data.state import State


def header() -> rx.Component:
    """Header component for Aero Data with navigation."""
    nav_links: list[tuple[str, str]] = [
        ("Home", "/"),
        ("Status", "/status"),
        # ("OpenAir Converter", "/openair-converter"),
        # ("GeoJSON", "/geojson"),
        # ("AIP to OpenAIR", "/aip-to-openair"),
    ]

    def nav_item(name: str, href: str) -> rx.Component:
        # Use rx.cond to determine if this link is active.
        return rx.cond(
            State.current_page == href,
            rx.link(
                rx.text(
                    name,
                    weight="bold",
                    color=rx.color("blue", 11),
                    underline=True,
                ),
                href=href,
                style={"marginRight": "1.5rem"},
                aria_current="page",
            ),
            rx.link(
                rx.text(
                    name,
                    weight="regular",
                    color=rx.color("gray", 11),
                    underline=False,
                ),
                href=href,
                style={"marginRight": "1.5rem"},
            ),
        )

    return rx.container(
        rx.vstack(
            rx.heading("Aero Data", size="9", color=rx.color("blue", 11)),
            rx.text(
                "Helping you with your aeronautical data needs since 2025.",
                font_family="monospace",
                size="2",
                color=rx.color("gray", 11),
            ),
            rx.hstack(
                *(nav_item(name, href) for name, href in nav_links),
                spacing="2",
            ),
            spacing="2",
        ),
        as_="header",
        padding_y="2",
        padding_x="4",
        border_bottom=f"1px solid {rx.color('gray', 6)}",
        max_width="800px",
        margin_x="auto",
        width="100%",
    )
