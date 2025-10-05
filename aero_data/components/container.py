import reflex as rx


def main_container(*children: rx.Component) -> rx.Component:
    return rx.container(
        rx.vstack(children, spacing="6"),
        size="1",
        padding="2rem",
        width="100%",
        height="100vh",
        background_color=rx.color("slate", 2),
    )
