import reflex as rx


def main_container(*children: rx.Component) -> rx.Component:
    return rx.container(
        rx.vstack(children, spacing="6"),
        size="1",
        padding="2rem",
        height="100%",
    )
