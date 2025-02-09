from unittest.mock import MagicMock, patch

import pytest
from utils.naviter.cup import CupFile

# Sample test data for CUP file content
CUP_FILE_CONTENT = """latitude,longitude,elevation,name,style
4642.516N,01404.583E,100m,"Waypoint 1",2
4642.416N,01403.400E,150ft,"Waypoint 2",3
4624.483N,01453.583E,200m,"Waypoint 3",4
4643.883N,01355.900E,300ft,"Waypoint 4",5
"""
EMPTY_CUP_FILE = ""


@pytest.fixture
def cup_file():
    """Fixture to return an instance of CupFile."""
    return CupFile()


@pytest.fixture
def mock_from_path():
    mock_from_path = MagicMock()
    mock_from_path.best.return_value = ""

    with patch("utils.file_handling.from_path", return_value=mock_from_path):
        yield mock_from_path


def test_loads(cup_file):
    """Test the loading of content via the loads() method."""
    cup_file.loads(CUP_FILE_CONTENT)
    assert len(cup_file.waypoints) == 4
    assert cup_file.waypoints[0].name == "Waypoint 1"


def test_load_empty_file(cup_file, mock_from_path):
    """Test loading an empty file."""
    mock_from_path.best.return_value = ""
    cup_file.load("empty.cup")
    assert len(cup_file.waypoints) == 0


def test_load_file(cup_file, mock_from_path):
    """Test loading a valid file."""

    mock_from_path.best.return_value = CUP_FILE_CONTENT

    result = cup_file.load("valid.cup")

    assert result is not None
    assert len(cup_file.waypoints) == 4
    assert cup_file.waypoints[0].name == "Waypoint 1"
    assert cup_file.waypoints[1].name == "Waypoint 2"


def test_landables(cup_file):
    """Test filtering landable waypoints."""
    cup_file.loads(CUP_FILE_CONTENT)
    landables = cup_file.landables()
    assert len(landables) == 4
    assert landables[0].name == "Waypoint 1"
    assert landables[1].name == "Waypoint 2"


def test_airports(cup_file):
    """Test filtering airports."""
    cup_file.loads(CUP_FILE_CONTENT)
    airports = cup_file.airports()
    assert len(airports) == 3  # Waypoints with style 2, 4, 5
    assert airports[0].name == "Waypoint 1"  # style 2


def test_outlandings(cup_file):
    """Test filtering outlanding waypoints."""
    cup_file.loads(CUP_FILE_CONTENT)
    outlandings = cup_file.outlandings()
    assert len(outlandings) == 1  # Only one with style 3
    assert outlandings[0].name == "Waypoint 2"  # style 3


def test_bbox(cup_file):
    """Test getting bounding box for the waypoints."""
    cup_file.loads(CUP_FILE_CONTENT)
    bbox = cup_file.bbox()
    assert bbox == (
        46.40805,
        13.931666666666667,
        46.73138333333333,
        14.89305,
    )  # min_lat, min_lon, max_lat, max_lon


def test_bbox_no_waypoints(cup_file):
    """Test bounding box when there are no waypoints."""
    assert cup_file.bbox() is None


def test_dumps(cup_file):
    """Test dumping the serialized content as a string."""
    cup_file.loads(CUP_FILE_CONTENT)
    serialized_content = cup_file.dumps()
    assert "Waypoint 1" in serialized_content
    assert "Waypoint 4" in serialized_content
