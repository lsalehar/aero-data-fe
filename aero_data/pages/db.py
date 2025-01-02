import reflex as rx


@rx.page(route="/db")
def db() -> rx.Component:
    return rx.container()
