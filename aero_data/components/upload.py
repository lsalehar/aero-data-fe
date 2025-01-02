import reflex as rx


def render_file(text):
    return rx.box(rx.text(text), display="flex", flex_grow=1)


upload_style = {
    "height": "3rem",
    "border_radius": "0.5rem",
    "padding": "0 !important",
    "padding_x": "0.5rem",
    "display": "flex",
    "align_items": "center",
    "justify_content": "center",
    "width": "100%",
}


def upload(
    id_: str, accept: dict, *upload_content: rx.Component, drop_handler=None
) -> rx.Component:
    return rx.cond(
        ~rx.selected_files(id_),
        rx.upload(
            *upload_content,
            accept=accept,
            multiple=False,
            max_files=1,
            on_drop=drop_handler,
            id=id_,
            border=f"1px solid {rx.color("blue", shade=7)}",
            background_color=rx.color("blue", shade=2),
            height="3rem",
            border_radius="0.25rem",
            padding="0",
            padding_x="0.5rem",
            display="flex",
            align_items="center",
            justify_content="center",
            width="100%",
        ),
        rx.box(
            rx.foreach(rx.selected_files(id_), render_file),
            rx.button(
                rx.icon("x", size=16),
                variant="outline",
                on_click=rx.clear_selected_files(id_),
                color_scheme="gray",
                radius="full",
            ),
            border=f"1px solid {rx.color("gray", shade=7)}",
            height="3rem",
            border_radius="0.25rem",
            padding="0",
            padding_x="0.5rem",
            display="flex",
            align_items="center",
            justify_content="center",
            width="100%",
        ),
    )
