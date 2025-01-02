import reflex as rx
from aero_data.components import main_container
from aero_data.components.upload import upload


@rx.page(route="/test")
def test() -> rx.Component:
    return main_container(
        upload(
            "upload",
            {"text/cup": [".cup"]},
            rx.text("Drop or ", rx.button("select", size="3", variant="ghost"), " a CUP file."),
        ),
    )
