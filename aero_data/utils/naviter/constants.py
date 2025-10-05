import re

CUP_FIELDS = (
    "name",
    "code",
    "country",
    "lat",
    "lon",
    "elev",
    "style",
    "rwdir",
    "rwlen",
    "rwwidth",
    "freq",
    "desc",
    "userdata",
    "pics",
)

CUP_DISTANCE_REGEX = re.compile(r"([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)(ft|m|nm|ml)", re.IGNORECASE)
CUP_LAT_REGEX = re.compile(r"(\d{2})(\d{2}\.\d{1,3})(n|s)", re.IGNORECASE)
CUP_LON_REGEX = re.compile(r"(\d{3})(\d{2}\.\d{1,3})(e|w)", re.IGNORECASE)
CUP_FREQ_REGEX = re.compile(r"^(118|119|12[0-9]|13[0-6])\.(?:\d{2}[05]|\d{2}|\d)$|")

CUP_LAT_FORMAT = "{deg:02d}{dec_min:06.3f}{dir}"
CUP_LON_FORMAT = "{deg:03d}{dec_min:06.3f}{dir}"
CUP_ELEV_FORMAT = "{elev:.1}{unit}"

CUP_SYTLE_MAPPING = {
    0: "Unknown",
    1: "Waypoint",
    2: "Airfield (Grass runway)",
    3: "Outlanding",
    4: "Gliding airfield",
    5: "Airfield (Solid runway)",
    6: "Mountain Pass",
    7: "Mountain Top",
    8: "Transmitter Mast",
    9: "VOR",
    10: "NDB",
    11: "Cooling Tower",
    12: "Dam",
    13: "Tunnel",
    14: "Bridge",
    15: "Power Plant",
    16: "Castle",
    17: "Intersection",
    18: "Marker",
    19: "Control/Reporting Point",
    20: "PG Take Off",
    21: "PG Landing Zone",
}

CUP_FIELDS_MAPPING = {
    "name": ["name", "waypoint", "wpname"],
    "code": ["code", "shortname", "short_name"],
    "country": ["country", "cntry"],
    "lat": ["lat", "la", "latitude"],
    "lon": ["lon", "lo", "long", "longitude"],
    "elev": ["elev", "elevation", "alt", "altitude"],
    "style": ["style", "type"],
    "rwdir": ["rwdir", "rw_dir", "rwy_dir", "runway_direction"],
    "rwlen": ["rwlen", "rw_len", "rwy_len", "runway_length"],
    "rwwidth": ["rwwidth", "rw_width", "rwy_width", "runway_width"],
    "freq": ["freq", "frequency"],
    "desc": ["desc", "description"],
    "userdata": ["userdata", "user_data"],
    "pics": ["pics", "pictures", "user_pictures"],
}
