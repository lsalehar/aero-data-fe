from datetime import datetime
from typing import List, Optional

from postgrest.base_request_builder import APIResponse
from pydantic import BaseModel
from shapely import Point, wkb, wkt

from aero_data.utils.naviter import CupWaypoint
from aero_data.utils.openaip import AirportType


class Country(BaseModel):
    id: int
    name: str
    iso2: str
    iso3: str
    local_name: Optional[str] = None
    region: Optional[str] = None


class Airport:

    def __init__(
        self,
        name: str,
        country: Country,
        location: Point | str | bytes,  # type: ignore
        elev: int,
        style: int,
        apt_type: AirportType,
        source_id: str,
        id: Optional[int] = None,
        code: Optional[str] = None,
        rw_dir: Optional[int] = None,
        rw_len: Optional[int] = None,
        rw_width: Optional[int] = None,
        freq: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.code = code
        self.country = country
        self.location = location
        self.elev = elev
        self.style = style
        self.apt_type = apt_type
        self.rw_dir = rw_dir
        self.rw_len = rw_len
        self.rw_width = rw_width
        self.freq = freq
        self.source_id = source_id
        self.created_at = created_at
        self.updated_at = updated_at

    @property
    def location(self) -> Point:
        return self._location

    @location.setter
    def location(self, value: Point | str | bytes):
        if isinstance(value, Point):
            self._location = value
            return

        if isinstance(value, str):
            try:
                parsed = wkt.loads(value)
            except Exception:
                parsed = wkb.loads(value)

            if not isinstance(parsed, Point):
                raise ValueError("Provided WKT is not a Point")
        elif isinstance(value, bytes):
            parsed = wkb.loads(value)
            if not isinstance(parsed, Point):
                raise ValueError("Provided WKB is not a Point")
        else:
            raise ValueError("Provided location is not a valid type")

        self._location = parsed

    def to_dict(self, exclude: Optional[List[str]] = []):
        apt_dict = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "country": self.country.iso2,
            "location": wkt.dumps(self.location),
            "elev": self.elev,
            "style": self.style,
            "apt_type": self.apt_type.value,
            "rw_dir": self.rw_dir,
            "rw_len": self.rw_len,
            "rw_width": self.rw_width,
            "freq": self.freq,
            "source_id": self.source_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if exclude:
            return {k: v for k, v in apt_dict.items() if k not in exclude}
        else:
            return apt_dict

    def to_db_dict(self):
        return {
            "name": self.name,
            "code": self.code,
            "country": self.country.iso2,
            "location": wkt.dumps(self.location),
            "elev": self.elev,
            "style": self.style,
            "apt_type": self.apt_type.value,
            "rw_dir": self.rw_dir,
            "rw_len": self.rw_len,
            "rw_width": self.rw_width,
            "freq": self.freq,
            "source_id": self.source_id,
        }

    def to_cup(self) -> CupWaypoint:
        return CupWaypoint(
            name=self.name,
            lat=self.location.y,
            lon=self.location.x,
            code=self.code,
            country=self.country.iso2,
            elev=self.elev,
            style=self.style,
            rwdir=self.rw_dir,
            rwlen=self.rw_len,
            rwwidth=self.rw_width,
            freq=self.freq,
        )


class Countries(BaseModel):
    countries: List[Country] = []

    @classmethod
    def populate_data(cls, response: APIResponse) -> "Countries":
        return cls(countries=[Country(**item) for item in response.data])

    def get_by_iso2(self, iso2: str) -> Country:
        for country in self.countries:
            if country.iso2 == iso2.upper():
                return country

        raise ValueError(f"Country with ISO2 {iso2} not found")
