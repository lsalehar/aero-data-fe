import django
import pytest
from django.conf import settings

from utils.naviter.waypoint import CupWaypoint

if not settings.configured:
    django.setup()


def test_initialization():
    minimal_waypoint = CupWaypoint(name="Test Point ", lat=" 4649.56N ", lon=" 01336.84E ")
    assert minimal_waypoint.name == "Test Point"
    assert minimal_waypoint.lat == 46.826
    assert minimal_waypoint.lon == 13.614

    full_waypoint = CupWaypoint(
        name=" Full Test Point",
        code=" FULLWPT01 ",
        country="at",  # Wrong case
        lat=46.826,
        lon=13.641,
        elev="1500ft",
        style=2,
        rwdir="090",
        rwlen="800m",
        rwwidth="20m",
        freq="123.5",
        userdata="Data",
        desc=" A full description\nWith\nmultiple lines. ",
        pics="image.jpg",
    )
    assert full_waypoint.name == "Full Test Point"
    assert full_waypoint.code == "FULLWPT01"
    assert full_waypoint.country == "AT"
    assert full_waypoint.lat == 46.826
    assert full_waypoint.lon == 13.641
    assert pytest.approx(full_waypoint.elev) == 457.2
    assert full_waypoint.style == 2
    assert full_waypoint.rwdir == 90
    assert full_waypoint.rwlen == 800
    assert full_waypoint.rwwidth == 20
    assert full_waypoint.freq == "123.5"
    assert full_waypoint.userdata == "Data"
    assert full_waypoint.desc == "A full description\nWith\nmultiple lines."
    assert full_waypoint.pics == "image.jpg"

    with pytest.raises(ValueError):
        CupWaypoint("", 46.5, 13.4)

    with pytest.raises(ValueError):
        CupWaypoint("Test Name", "", 13.4)

    with pytest.raises(ValueError):
        CupWaypoint("Test Name", 13.4, "")

    with pytest.raises(ValueError):
        CupWaypoint("Test Waypoint", 91.1, 34.4)

    with pytest.raises(ValueError):
        CupWaypoint("Test Waypoint", -91.1, 34.4)

    with pytest.raises(ValueError):
        CupWaypoint("Test Waypoint", -34.4, 182.1)

    with pytest.raises(ValueError):
        CupWaypoint("Test Waypoint", 34.4, -182.1)


def test_getters_setters():
    waypoint = CupWaypoint(name="Initial", lat=46, lon=13)
    # Name
    waypoint.name = "Changed Name"
    assert waypoint.name == "Changed Name"

    # Lat
    with pytest.raises(ValueError):
        waypoint.lat = "invalid"

    with pytest.raises(ValueError):
        waypoint.lat = "9100.0N"

    with pytest.raises(ValueError):
        waypoint.lat = 91

    waypoint.lat = "4642.00N"
    assert waypoint.lat == 46.7

    waypoint.lat = 46
    assert waypoint.lat == 46.0

    # Lon
    with pytest.raises(ValueError):
        waypoint.lon = "invalid"

    with pytest.raises(ValueError):
        waypoint.lon = "18100.0W"

    with pytest.raises(ValueError):
        waypoint.lon = -181

    waypoint.lon = "01330.0E"
    assert waypoint.lon == 13.5

    waypoint.lon = 13
    assert waypoint.lon == 13.0
