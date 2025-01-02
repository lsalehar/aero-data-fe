import csv
from io import StringIO
from typing import Any, Callable, Optional

from cuid2 import Cuid
from shapely.geometry import Point

from aero_data.utils.naviter.constants import CUP_FIELDS
from aero_data.utils.naviter.helpers import (
    convert_distance_to_m_and_og_unit,
    convert_lat_lon_to_dd,
    format_decimal_degrees_to_cup,
    format_distance,
    is_valid_cup_freq,
    is_valid_style,
)


class CountriesLoader:
    """Singleton to lazily load the Countries instance."""

    _countries = None

    @classmethod
    def get_countries(cls):
        if cls._countries is None:
            from aero_data import (
                countries,  # Import lazily to avoid circular dependencies
            )

            cls._countries = countries
        return cls._countries


class CupWaypoint:
    # The `CupWaypoint` class represents a cup waypoint with various attributes such as name, code,
    # coordinates, elevation, style, and other details. The values are always stored as SI units.

    _cup_fields = CUP_FIELDS

    def __init__(
        self,
        name: str,
        lat: str | float,
        lon: str | float,
        code: Optional[str] = None,
        country: Optional[str] = None,
        elev: Optional[str | float] = None,
        style: Optional[str | int] = None,
        rwdir: Optional[str | int] = None,
        rwlen: Optional[str | float] = None,
        rwwidth: Optional[str | float] = None,
        freq: Optional[str] = None,
        userdata: Optional[str] = None,
        desc: Optional[str] = None,
        pics: Optional[str] = None,
    ) -> None:
        if not name:
            raise ValueError("Waypoint requires a name")
        if not lat or not lon:
            raise ValueError("Both lat. and lon. must be specified.")

        self._id = Cuid().generate()
        self._update_coordinates(lat, lon)
        self.name = name
        self.code = code
        self.country = country
        self.elev = elev
        self.style = style
        self.rwdir = rwdir
        self.rwlen = rwlen
        self.rwwidth = rwwidth
        self.freq = freq
        self.desc = desc
        self.userdata = userdata
        self.pics = pics
        self._countries = None

    @property
    def name(self):
        return self._name  # type: ignore

    @name.setter
    def name(self, value):
        self._set_string_attr(value, "name")

    @property
    def code(self):
        return self._code  # type: ignore

    @code.setter
    def code(self, value):
        self._set_string_attr(value, "code")

    @property
    def country(self):
        return self._country

    @country.setter
    def country(self, value):
        if not value or value is None:
            self._country = None
        elif value and isinstance(value, str) and len(value) == 2:
            if value in ["--"]:
                self._country = None
            else:
                countries = CountriesLoader.get_countries()
                country = countries.get_by_iso2(value.upper())  # type:ignore
                if country:
                    self._set_string_attr(value.upper(), "country")
                else:
                    raise ValueError(f"Invalid ISO 3166-a alpha-2 country code: {value}")
        else:
            raise ValueError("Country code must be a two-letter string.")

    @property
    def lat(self):
        return self._lat

    @lat.setter
    def lat(self, value):
        self._update_coordinates(value, self.lon)

    @property
    def lon(self):
        return self._lon

    @lon.setter
    def lon(self, value):
        self._update_coordinates(self.lat, value)

    def _update_coordinates(self, lat, lon):
        if isinstance(lat, (str, float, int)) and isinstance(lon, (str, float, int)):
            self._lat = convert_lat_lon_to_dd(lat) if isinstance(lat, str) else lat
            self._lon = convert_lat_lon_to_dd(lon) if isinstance(lon, str) else lon
            if not (-90 <= self._lat <= 90):
                raise ValueError(
                    f"Lattitude must be between -90 and 90 degrees, is: {self._lat}"
                )
            if not (-180 <= self._lon <= 180):
                raise ValueError(
                    f"Longitude must be between -1880 and 180 deg., is: {self._lon}"
                )
            self.coordinates = Point(self._lon, self._lat)
        else:
            raise ValueError(
                "Latitude and longitude must be valid numeric or cup string types."
            )

    @property
    def elev(self):
        return self._elev  # type: ignore

    @elev.setter
    def elev(self, value):
        self._set_distance_attr(value, "elev")

    @property
    def style(self):
        return self._style  # type: ignore

    @style.setter
    def style(self, value):
        self._set_integer_attr(value, "style", is_valid_style)

    @property
    def rwdir(self):
        return self._rwdir  # type: ignore

    @rwdir.setter
    def rwdir(self, value):
        self._set_integer_attr(value, "rwdir")

    @property
    def rwlen(self):
        return self._rwlen  # type: ignore

    @rwlen.setter
    def rwlen(self, value):
        self._set_distance_attr(value, "rwlen")

    @property
    def rwwidth(self):
        return self._rwwidth  # type: ignore

    @rwwidth.setter
    def rwwidth(self, value):
        self._set_distance_attr(value, "rwwidth")

    @property
    def freq(self):
        return self._freq  # type: ignore

    @freq.setter
    def freq(self, value):
        self._set_string_attr(value, "freq", is_valid_cup_freq)

    @property
    def userdata(self):
        return self._userdata  # type: ignore

    @userdata.setter
    def userdata(self, value):
        self._set_string_attr(value, "userdata")

    @property
    def desc(self):
        return self._desc  # type: ignore

    @desc.setter
    def desc(self, value):
        self._set_string_attr(value, "desc")

    @property
    def pics(self):
        return self._pics  # type: ignore

    @pics.setter
    def pics(self, value):
        self._set_string_attr(value, "pics")

    def get_point(self) -> Point:
        return Point(self.lon, self.lat)

    def _set_distance_attr(self, value, attr_name):
        storage_attr = f"_{attr_name}"
        og_unit_attr = f"_og_{attr_name}_unit"
        if not value:
            setattr(self, storage_attr, None)
            setattr(self, og_unit_attr, "m")
        elif isinstance(value, str):
            try:
                converted_value, original_unit = convert_distance_to_m_and_og_unit(value)
                setattr(self, storage_attr, converted_value)
                setattr(self, og_unit_attr, original_unit)
            except ValueError as e:
                raise ValueError(f"Invalid value for '{attr_name}': {value}. {str(e)}")
        elif isinstance(value, (int, float)):
            setattr(self, storage_attr, value)
            # Assuming the value is given in meters if directly a number
            setattr(self, og_unit_attr, "m")
        else:
            raise ValueError(
                f"Invalid value type {type(value).__name__} for '{attr_name}' attribute."
            )

    def _set_string_attr(
        self, value, attr_name: str, vali_fn: Optional[Callable[[str], bool]] = None
    ):
        storage_attr = f"_{attr_name}"
        if not value:
            setattr(self, storage_attr, None)
        elif isinstance(value, str):
            if vali_fn is None or vali_fn(value):
                setattr(self, storage_attr, value.strip())
            else:
                raise ValueError(f"Value '{value}' is invalid for '{attr_name}' attribute.")
        else:
            raise ValueError(
                f"Invalid value type {type(value).__name__}:{value} for '{attr_name}' attribute."
            )

    def _set_integer_attr(
        self, value: Any, attr_name: str, vali_fn: Optional[Callable[[int | str], bool]] = None
    ):
        storage_attr = f"_{attr_name}"
        if not value or value is None:
            setattr(self, storage_attr, None)
        elif isinstance(value, (int, str)):
            if vali_fn is None or vali_fn(value):
                setattr(self, storage_attr, int(value))
            else:
                raise ValueError(f"Value '{value} is invalid for '{attr_name}' attribute")
        else:
            raise ValueError(
                f"Invalid value type {type(value).__name__}:{value} for '{attr_name}' attribute."
            )

    def is_landable(self):
        return self.style in [2, 3, 4, 5]

    def is_airport(self):
        return self.style in [2, 4, 5]

    def is_outlanding(self):
        return self.style in [3]

    def _format_attr(self, attr):
        if attr in ("lat", "lon"):
            return format_decimal_degrees_to_cup(getattr(self, attr), is_lat=(attr == "lat"))
        elif attr in ("elev", "rwlen", "rwwidth"):
            return format_distance(getattr(self, attr), getattr(self, f"_og_{attr}_unit", "m"))
        elif getattr(self, attr) is None:
            return ""
        return str(getattr(self, attr)) or ""

    def __str__(self):
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self._cup_fields,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        waypoint_data = {attr: self._format_attr(attr) for attr in self._cup_fields}
        writer.writerow(waypoint_data)  # type: ignore
        result = output.getvalue()
        output.close()
        return result.strip("\r\n")

    def __repr__(self):
        return f"CupWaypoint({self.name}, {self.lon:0.6f}, {self.lat:0.6f}, _id={self._id})"
