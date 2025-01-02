import reflex as rx
from aero_data.pages import index, status, test

app = rx.App(theme=rx.theme(accent_color="blue", gray_color="slate", color_mode="inherit"))  # type: ignore
app.add_page(index)
app.add_page(status)
app.add_page(test)
