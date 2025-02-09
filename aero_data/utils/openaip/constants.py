from enum import Enum

# Airport
# If adding types here, add them to the model as well.
APT_TYPE = {
    0: "Airport (civil/military)",
    1: "Glider Site",
    2: "Airfield Civil",
    3: "International Airport",
    4: "Heliport Military",
    5: "Military Aerodrome",
    6: "Ultra Light Flying Site",
    7: "Heliport Civil",
    8: "Aerodrome Closed",
    9: "Airport resp. Airfield IFR",
    10: "Airfield Water",
    11: "Landing Strip",
    12: "Agricultural Landing Strip",
    13: "Altiport",
}


class AirportType(int, Enum):
    AIRPORT = 0
    GLIDER_SITE = 1
    AIRPORT_CIVIL = 2
    AIRPORT_INTL = 3
    HELIPORT_MIL = 4
    AERODROME_MIL = 5
    UL_SITE = 6
    HELIPORT_CIVIL = 7
    CLOSED = 8
    AIRPORT_IFR = 9
    AIRPORT_WATER = 10
    LANDING_STRIP = 11
    LANDING_STRIP_AGRIC = 12
    ALTIPORT = 13
    UNKNOWN = 999
