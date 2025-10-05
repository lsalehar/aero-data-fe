import reflex as rx

from aero_data.components import footer, header, main_container, switch, upload
from aero_data.state import UpdateCupFile


def metric(label: str, value: rx.Var | str | int) -> rx.Component:  # type: ignore
    return rx.card(
        rx.vstack(
            rx.text(label, size="1", color=rx.color("gray", 11)),
            rx.heading(value, size="6"),
            spacing="1",
            align="start",
        ),
        padding="0.75rem",
    )


def update_airports_card(*children) -> rx.Component:
    return rx.card(
        rx.flex(
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "Update airports in your CUP file", size="4", weight="bold"
                    ),
                    rx.text("Fill the form to get an updated file", size="3"),
                    spacing="1",
                    height="100%",
                    width="100%",
                    align_items="start",
                ),
                rx.badge(
                    rx.icon(tag="plane-landing", size=32),
                    color_scheme="blue",
                    radius="full",
                    padding="0.65rem",
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
        background_color=rx.color("white", 1),
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
        rx.hstack(
            rx.text("Accepted: .cup", size="1", color=rx.color("gray", 11)),
            rx.button(
                "Try a sample file",
                size="1",
                variant="soft",
                on_click=UpdateCupFile.download_sample,
            ),
            align="center",
            spacing="3",
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
            rx.text(
                "Data from: ",
                rx.link(
                    "OpenAIP",
                    href="https://www.openaip.net",
                ),
                size="1",
                color_scheme="gray",
            ),
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
            align="end",
            justify="between",
        ),
        direction="column",
        spacing="3",
    )


def upload_form(upload_id: str) -> rx.Component:
    return update_airports_card(
        rx.match(
            UpdateCupFile.stage,
            (
                UpdateCupFile.RUNNING,
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("Updating...", size="2", color=rx.color("gray", 11)),
                        spacing="2",
                    ),
                    min_height="8rem",
                ),
            ),
            (
                UpdateCupFile.DONE,
                rx.vstack(
                    rx.card(
                        rx.hstack(
                            rx.icon("check", color=rx.color("green", 9)),
                            rx.heading("Update complete", size="4"),
                            justify="start",
                            spacing="2",
                        ),
                        rx.hstack(
                            metric("Updated", UpdateCupFile.updated_count),
                            metric("Added", UpdateCupFile.added_count),
                            metric("Deleted", UpdateCupFile.deleted_count),
                            metric("Not found", UpdateCupFile.not_found_count),
                            metric("Not updated", UpdateCupFile.not_updated_count),
                            spacing="3",
                            wrap="wrap",
                        ),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.button(
                            "Back",
                            variant="outline",
                            on_click=UpdateCupFile.reset_state(upload_id),
                            flex_grow=1,
                        ),
                        rx.button(
                            "Download updated file",
                            on_click=UpdateCupFile.download_zip,
                            flex_grow=1,
                        ),
                        rx.dialog.root(
                            rx.dialog.trigger(rx.button("View report", variant="soft")),
                            rx.dialog.content(
                                rx.dialog.title("Update report"),
                                rx.scroll_area(
                                    rx.code(
                                        UpdateCupFile.report_text,
                                        width="100%",
                                        max_height="50vh",
                                    )
                                ),
                                rx.hstack(
                                    rx.button(
                                        "Download report",
                                        on_click=UpdateCupFile.download_report,
                                        variant="soft",
                                    ),
                                    rx.dialog.close(
                                        rx.button("Close", variant="outline")
                                    ),
                                    justify="end",
                                    spacing="3",
                                ),
                            ),
                        ),
                        width="100%",
                        spacing="4",
                    ),
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
    return main_container(header(), upload_form(upload_id), footer())
