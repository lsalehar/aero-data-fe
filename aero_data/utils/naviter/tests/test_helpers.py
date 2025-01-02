from math import inf

import pytest

from utils.naviter.helpers import format_dd_lat_lon_to_cup
from utils.naviter.waypoint import (
    convert_distance_to_m_and_og_unit,
    convert_lat_lon_to_dd,
    format_decimal_degrees_to_cup,
    format_distance,
)


# Parameterized test for convert_lat_lon_to_dd()
@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("5107.830N", 51.1305),
        ("4500.000S", -45.0),
        ("01410.467E", 14.17445),
        ("17959.999W", -179.99998),
        ("0000.000N", 0.0),
        ("00000.000E", 0.0),
        ("9000.000N", 90.0),
        ("18000.000W", -180.0),
    ],
)
def test_convert_lat_lon_to_dd(input_value, expected):
    assert pytest.approx(convert_lat_lon_to_dd(input_value), 0.0001) == expected


# Handling errors in input with parameterization
@pytest.mark.parametrize("input_value", ["5107830N", "N5107.830", 5107.830])
def test_invalid_lat_lon_input(input_value):
    with pytest.raises(ValueError):
        convert_lat_lon_to_dd(input_value)


# Test for format_decimal_degrees()
@pytest.mark.parametrize(
    "degrees,is_lat,expected",
    [
        (51.1305, True, "5107.830N"),
        (-45.0, True, "4500.000S"),
        (14.17445, False, "01410.467E"),
        (-179.99998, False, "17959.999W"),
        (0, True, "0000.000N"),
        (0, False, "00000.000E"),
    ],
)
def test_format_decimal_degrees(degrees, is_lat, expected):
    assert format_decimal_degrees_to_cup(degrees, is_lat) == expected


# Test data for formatting latitude and longitude in the CUP format
@pytest.mark.parametrize(
    "lat, lon, expected_lat, expected_lon",
    [
        (51.1305, 14.17445, "5107.830N", "01410.467E"),
        (-45.0, -179.99998, "4500.000S", "17959.999W"),
        (0, 0, "0000.000N", "00000.000E"),
        (90.0, 180.0, "9000.000N", "18000.000E"),
        (-90.0, -180.0, "9000.000S", "18000.000W"),
    ],
)
def test_format_dd_lat_lon_to_cup(lat, lon, expected_lat, expected_lon):
    formatted_lat, formatted_lon = format_dd_lat_lon_to_cup(lat, lon)
    assert formatted_lat == expected_lat
    assert formatted_lon == expected_lon


# Test cases to ensure that the function can handle extreme values and boundaries
@pytest.mark.parametrize("lat, lon", [(90.0001, 180.0001), (-90.0001, -180.0001), (100, -200)])
def test_format_dd_lat_lon_to_cup_boundaries(lat, lon):
    with pytest.raises(ValueError):
        format_dd_lat_lon_to_cup(lat, lon)


# Test to ensure the function handles non-numeric inputs
@pytest.mark.parametrize(
    "lat, lon",
    [
        ("not a number", "also not a number"),
        ("45.2N", "131.876W"),  # Incorrect format but valid strings
    ],
)
def test_format_dd_lat_lon_to_cup_non_numeric(lat, lon):
    with pytest.raises(TypeError):
        format_dd_lat_lon_to_cup(lat, lon)


# Tests for elevation conversion and formatting
@pytest.mark.parametrize(
    "input_value,expected_output,expected_unit",
    [
        ("504.0m", 504.0, "m"),
        ("1000ft", 304.8, "ft"),
        ("-200m", -200, "m"),
        ("-500ft", -152.4, "ft"),
        ("3.280839895013123e2ft", 100, "ft"),
        ("-3.280839895013123e2ft", -100, "ft"),
    ],
)
def test_convert_distance_to_meters_and_unit(input_value, expected_output, expected_unit):
    result, unit = convert_distance_to_m_and_og_unit(input_value)
    assert result == pytest.approx(expected_output)
    assert unit == expected_unit


def test_convert_distance_to_meters_and_unit_empty_string():
    result, unit = convert_distance_to_m_and_og_unit("")
    assert result == -inf
    assert unit == "m"


def test_convert_distance_to_meters_and_unit_failure():
    with pytest.raises(ValueError):
        convert_distance_to_m_and_og_unit("1000")


# Tests for distance formatting
@pytest.mark.parametrize(
    "dist_in_m, unit, expected",
    [
        (304.8, "ft", "1000ft"),  # Basic conversion to feet
        (1852, "nm", "1.00nm"),  # Basic conversion to nautical miles
        (1609.34, "ml", "1.00ml"),  # Basic conversion to miles
        (100, "m", "100.0m"),  # Basic conversion to meters
        (float("-inf"), "ft", ""),  # Edge case for infinite negative distance
        (152.4, "ft", "500ft"),  # Edge case for rounding feet
        (0, "m", "0.0m"),  # Zero distance
        (500, "nm", "0.27nm"),  # Rounding nautical miles
        (500, "ml", "0.31ml"),  # Rounding nautical miles
    ],
)
def test_format_distance(dist_in_m, unit, expected):
    assert format_distance(dist_in_m, unit) == expected
