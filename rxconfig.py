import reflex as rx
import toml
from reflex.plugins.sitemap import SitemapPlugin


def get_version():
    pyproject_data = toml.load("pyproject.toml")
    return pyproject_data["project"]["version"]


config = rx.Config(
    app_name="aero_data",
    version=get_version(),
    show_built_with_reflex=False,
    disable_plugins=[SitemapPlugin],
)
