import io
import json
import os
import time
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import IO, Optional, Tuple, Union

import requests
from charset_normalizer import from_path
from tqdm import tqdm


def get_utf8_content(file_path: str, steps: int = 3) -> str:
    """
    Returns the UTF-8 encoded content of a file.

    Args:
        file_path (str): Path to the file.
        steps (int, optional): Number of decoding attempts. Default is 3.

    Returns:
        str: UTF-8 encoded content of the file.
    """
    content = from_path(file_path, steps=steps).best()
    return str(content) if content else ""


def save_raw(data, filename, path):
    """
    Saves raw binary data to a specified file.

    Args:
        data (bytes): The binary data to save.
        filename (str): The name of the file.
        path (str): The directory path to save the file.

    Returns:
        None
    """
    file_path = Path(path) / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("wb") as f:
        f.write(data)


def load_json(path):
    """
    Loads a json.

    Args:
        path (str): Path of the file to load

    Returns:
        Any: Contents of the json file
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(json_data, json_file_path, minified=False):

    separators = (",", ":") if minified else None
    indent = None if minified else 4
    if path := os.path.dirname(json_file_path):
        os.makedirs(path, exist_ok=True)

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(
            json_data,
            f,
            indent=indent,
            separators=separators,
            ensure_ascii=False,
            allow_nan=False,
        )


def download_file(
    url: str,
    destination: Optional[str] = None,
    file_name: Optional[str] = None,
    params: Optional[dict] = None,
    silent: bool = False,
) -> Tuple[str, StringIO | str | BytesIO | None]:
    """Downloads a file from a URL to a local destination.

    Displays a progress bar while downloading. Automatically detects if file is text or binary.

    Args:
        url (str): URL of file to download.
        destination (Optional[str], optional): Local destination path to save file. Defaults to None.
        file_name (Optional[str]): Specify file name if url does not contain it.
        params (Optional[dict]): Parameters to be included in the url for the request

    Returns:
        str: Original file name
        Union[str, IO[str], IO[bytes]]: File contents as StringIO or BytesIO if no destination
        specified, otherwise returns destination path.

    Raises:
        requests.HTTPError: If download fails."""

    buffer: Optional[Union[IO[str], IO[bytes]]] = None
    response = requests.head(url)
    total_size = int(response.headers.get("content-length", 0))
    name = file_name if file_name else url.split("/")[-1]
    is_text = "text" in response.headers.get(
        "Content-Type", ""
    ) or "json" in response.headers.get("Content-Type", "")

    if not silent:
        progress_bar = tqdm(total=total_size, unit="B", unit_scale=True, desc=name)

    with requests.get(url, params=params, stream=True) as response:
        response.raise_for_status()
        if destination:
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            mode = "w" if is_text else "wb"
            with open(destination, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not silent:
                        progress_bar.update(len(chunk))
                    if is_text:
                        f.write(chunk.decode(response.encoding or "utf-8"))
                    else:
                        f.write(chunk)
        else:
            buffer = io.StringIO() if is_text else io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if not silent:
                    progress_bar.update(len(chunk))
                if is_text:
                    buffer.write(chunk.decode(response.encoding or "utf-8"))
                else:
                    buffer.write(chunk)
            buffer.seek(0)

    if not silent:
        progress_bar.close()

    return name, buffer or destination


def extract_from_zip(
    zip_file: IO[bytes], file_extension: str = ""
) -> tuple[str | None, BytesIO] | None:
    """Extract a file with a specific extension from an in-memory zip file.

    :param zip_file: In-memory zip file.
    :param file_extension: The extension of the file to extract.
    :return: As in-memory file

    Args:
        file_endswith:
    """
    with zipfile.ZipFile(zip_file) as z:
        if matching_file := next(
            (name for name in z.namelist() if name.endswith(file_extension)), None
        ):
            with z.open(matching_file) as f:
                contents = io.BytesIO(f.read())
                return matching_file, contents

    return None


def is_file_older_than(file, days=1):
    file_time = os.path.getmtime(file)
    return (time.time() - file_time) / 3600 > 24 * days
