import reflex as rx

from aero_data.components import header, main_container, switch, upload
from aero_data.state import UpdateCupFile


def update_airports_card(*children) -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.badge(
                    rx.icon(tag="plane-landing", size=32),
                    color_scheme="blue",
                    radius="full",
                    padding="0.65rem",
                ),
                rx.vstack(
                    rx.heading("Update airports in your CUP file", size="4", weight="bold"),
                    rx.text("Fill the form to get an updated file", size="3"),
                    spacing="1",
                    height="100%",
                    align_items="start",
                ),
                height="100%",
                spacing="4",
                align_items="center",
                width="100%",
            ),
            children,
            direction="column",
            reset_on_submit=False,
            spacing="4",
        ),
        size="2",
        width="100%",
    )


def select_file(upload_id: str) -> rx.Component:
    return rx.flex(
        upload(
            upload_id,
            {"application/octet-stream": [".cup"]},
            rx.text(
                "Drop or ",
                rx.button("select", size="3", variant="ghost"),
                " a CUP file.",
            ),
        ),
        switch(
            "Update airport locations",
            "update_locations",
            default_checked=UpdateCupFile.update_locations,
            on_change=UpdateCupFile.set_update_locations,  # type:ignore
            tooltip_content="Updates the airport location with the one from our database.",
        ),
        switch(
            "Add missing airports",
            "delete_closed",
            default_checked=UpdateCupFile.add_missing,
            on_change=UpdateCupFile.set_add_missing,  # type:ignore
            tooltip_content=(
                "Airports located within the bounding box of all waypoints in the uploaded CUP file "
                "will be automatically added to the updated file."
            ),
        ),
        switch(
            "Remove closed airports",
            "delete_closed",
            default_checked=UpdateCupFile.delete_closed,
            on_change=UpdateCupFile.set_delete_closed,  # type:ignore
            tooltip_content="Remove closed airports from the cup file.",
        ),
        rx.flex(
            rx.button(
                "Update",
                size="3",
                variant="surface",
                disabled=~rx.selected_files(upload_id),
                on_click=UpdateCupFile.handle_upload(
                    rx.upload_files(upload_id)  # type:ignore
                ),
            ),
            flex_grow=1,
            justify="end",
        ),
        direction="column",
        spacing="3",
    )


def upload_form(upload_id: str) -> rx.Component:
    return update_airports_card(
        rx.match(
            UpdateCupFile.stage,
            (UpdateCupFile.RUNNING, rx.text("Updating...", align="center")),
            (
                UpdateCupFile.DONE,
                rx.flex(
                    rx.button(
                        "Back",
                        variant="outline",
                        on_click=UpdateCupFile.reset_state(upload_id),
                        flex_grow=1,
                    ),
                    rx.button(
                        "Download updated file.",
                        on_click=UpdateCupFile.download_zip,
                        flex_grow=1,
                    ),
                    flex_grow=1,
                    direction="row",
                    spacing="4",
                ),
            ),
            (
                UpdateCupFile.ERROR,
                rx.vstack(
                    rx.callout(
                        rx.text(
                            "An error occurred while processing the file:",
                            rx.text(UpdateCupFile.error_message, weight="regular"),
                            weight="medium",
                        ),
                        icon="triangle_alert",
                        color_scheme="red",
                        role="alert",
                    ),
                    rx.button(
                        "Back",
                        variant="outline",
                        on_click=UpdateCupFile.reset_state(upload_id),
                    ),
                ),
            ),
            select_file(upload_id),
        )
    )


@rx.page(route="/", on_load=UpdateCupFile.log_page_visit)
def index() -> rx.Component:
    upload_id = "upload_1"
    return main_container(
        header(),
        upload_form(upload_id),
    )
