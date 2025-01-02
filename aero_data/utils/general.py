import atexit
import io
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from json import JSONDecodeError
from math import isclose
from typing import Any, Callable, Dict, Iterable, List, Optional

from shapely import Point

from aero_data.utils.file_handling import load_json, write_json

logger = logging.getLogger(__name__)


def truncate_string(in_str, max_len=24):
    if len(in_str) > max_len:
        return in_str[: max_len - 1] + "…"
    return in_str


def chunked(iterable, size):
    """Yield successive chunks from iterable of given size."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def is_debugging():
    """
    Checks if the Python interpreter is running in debug mode.

    Returns:
        bool: True if debugging is enabled, False otherwise.
    """
    return hasattr(sys, "gettrace") and sys.gettrace() is not None


def values_equal(val1: Any, val2: Any, num_tol=1e-7):
    """
    Compares two values for equality, with optional tolerance for floats.

    Args:
        val1 (Any): The first value to compare.
        val2 (Any): The second value to compare.
        num_tol (float, optional): Absolute tolerance for float comparisons. Defaults to 1e-7.

    Returns:
        bool: True if the values are equal, False otherwise.
    """
    if val1 is None and val2 is None:
        return True

    if val1 is None or val2 is None:
        return False

    if type(val1) is not type(val2):
        return False

    if isinstance(val1, float):
        return isclose(val1, val2, abs_tol=num_tol)

    if isinstance(val1, Point):
        return val1.equals_exact(val2, num_tol)

    return val1 == val2


def has_changed(obj1: Any, obj2: Any, attributes: Iterable) -> bool:
    """
    Checks if the specified attributes of an instance have changed.

    Args:
        instance (Any): The object instance to check for changes.
        values (Dict[str, Any]): A dictionary where keys are attribute names and values are
        the expected values to compare against.

    Returns:
        bool: True if any attribute in the instance has a different value than provided in the
        values dict, False otherwise.
    """
    return any(
        not values_equal(getattr(obj1, attr, None), getattr(obj2, attr, None))
        for attr in attributes
    )


def update_instance(instance: Any, values: Dict[str, Any]) -> None:
    """
    Updates the attributes of an instance with the provided values.

    Args:
        instance (Any): The object instance to be updated.
        values (Dict[str, Any]): A dictionary where keys are attribute names and values are the
        new values to set on the instance.

    Returns:
        None
    """
    for key, val in values.items():
        setattr(instance, key, val)


def run_in_threads(
    func: Callable,
    arguments: list,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List:
    """
    Executes a function across multiple threads.

    Args:
        func (Callable): The function to execute.
        arguments (list): List of arguments to pass to the function.
        progress_callback (Optional[Callable[[int, int], None]]): Callback for progress updates. Defaults to None.

    Returns:
        List: Combined results of function executions.
    """
    results = []
    total = len(arguments)
    done = 0

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(func, arg) for arg in arguments]
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as exc:
                logger.error(f"Function failed: {exc}")
            finally:
                done += 1
                if progress_callback:
                    progress_callback(done, total)

    return results


def search_list_of_objects(
    list_of_objs: List[Any],
    search_attr: str,
    search_term: Any,
    additional_filter: Optional[Callable[[Any], bool]] = None,
) -> List:
    """
    Search a list of dicts or objects by attribute and optional filter.

    Args:
        list_of_objs (list): List of dicts or objects.
        srch_attribute (str): Attribute or key to search by.
        search_term (any): Value to match.
        additional_filter (func); Optional function to further filter results.

    Returns:
        list: List of results

    """
    results = []
    if all(isinstance(obj, dict) for obj in list_of_objs):
        results = [obj for obj in list_of_objs if obj.get(search_attr) == search_term]
    elif search_term is not None:
        results = [obj for obj in list_of_objs if getattr(obj, search_attr) == search_attr]

    if additional_filter:
        results = list(filter(additional_filter, results))

    return results


class Cache:
    """
    A simple key-value cache stored in a JSON file. Automatically saved on exit.

    Attributes:
        path (str): The file path for the cache data.
        timestamp (str): The last updated timestamp.
        data (dict): The cached key-value pairs.

    Methods:
        get(key, default=None): Retrieve a value by key.
        set(key, value): Set a value for a key and update the timestamp.
        clear(): Clear the cache and update the timestamp.
        save(): Save the current cache to the JSON file.
        size(): Return the number of items in the cache.
        is_empty(): Check if the cache is empty.
        is_in_data(key): Check if a key exists in the cache.
        is_expired(days=365): Check if the cache has expired.
        invalidate(): Invalidate the cache and clear the data.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._load()
        atexit.register(self.save)

    def _load(self):
        try:
            cache = load_json(self.path)
            self.timestamp = cache["timestamp"]
            self.data = cache["data"]
        except (FileNotFoundError, JSONDecodeError):
            self._update_timestamp()
            self.data = {}

    def _update_timestamp(self):
        self.timestamp = datetime.now().isoformat()

    def _dict(self):
        return {"timestamp": self.timestamp, "data": self.data}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self._update_timestamp()
        self.data[key] = value

    def clear(self):
        self._update_timestamp()
        self.data.clear()

    def save(self):
        write_json(self._dict(), self.path)

    def size(self):
        return len(self.data)

    def is_empty(self):
        return len(self.data) == 0

    def is_in_data(self, key):
        return key in self.data

    def is_expired(self, days=365):
        delta = datetime.now() - datetime.fromisoformat(self.timestamp)
        return delta.days >= days

    def invalidate(self):
        write_json(self._dict(), self.path.replace("json", "json.old"))
        self._update_timestamp()
        self.data.clear()


class LatLonCache(Cache):
    """
    A cache for storing data using latitude and longitude as keys.

    This class extends the Cache class, allowing for efficient retrieval and
    storage of data based on geographical coordinates.

    Attributes:
        path (str): The file path for the cache data inherited from the Cache class.

    Methods:
        get(lat, lon, default=None): Retrieve a value using latitude and longitude.
        set(lat, lon, value): Set a value for a specific latitude and longitude.
        is_in_data(lat, lon): Check if a value exists for the given coordinates.
    """

    def __init__(self, path: str) -> None:
        super().__init__(path)

    @staticmethod
    def _key(lat, lon):
        return f"{lat}, {lon}"

    def get(self, lat, lon, default=None):
        return super().get(self._key(lat, lon), default)

    def set(self, lat, lon, value):
        super().set(self._key(lat, lon), value)

    def is_in_data(self, lat, lon):
        return super().is_in_data(self._key(lat, lon))


def list_project_structure(
    root_dir: str,
    file: io.StringIO,
    ignore_dirs: list = [],
    ignore_file_endings: list = [],
    level: int = 0,
):

    indent = " " * 4 * level
    file.write(f"{indent}{os.path.basename(root_dir)}/\n")

    for item in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, item)
        if os.path.isdir(path):
            if item not in ignore_dirs:
                list_project_structure(path, file, ignore_dirs, ignore_file_endings, level + 1)
        else:
            if not any(item.endswith(ending) for ending in ignore_file_endings):
                file.write(f"{indent}    {item}\n")


if __name__ == "__main__":
    root = os.path.abspath(".")
    output_file_name = os.path.join(root, "structure.txt")

    ignore_dirs = [
        ".git",
        "__pycache__",
        ".ipynb_checkpoints",
        ".pytest_cache",
        ".mypy_cache",
        ".web",
        "raw_data",
        "cache_data",
    ]
    ignore_files = [
        ".cpg",
        ".dbf",
        ".prj",
        ".shp",
        ".shx",
        ".pyc",
        ".log",
        ".DS_store",
        ".shellcheckrc",
    ]

    with open(output_file_name, "w") as f:
        list_project_structure(
            root,
            f,  # type: ignore
            ignore_dirs,
            ignore_files,
        )
