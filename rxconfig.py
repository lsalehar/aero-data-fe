import reflex as rx
import toml


def get_version():
    pyproject_data = toml.load("pyproject.toml")
    return pyproject_data["tool"]["poetry"]["version"]


config = rx.Config(app_name="aero_data", version=get_version())
