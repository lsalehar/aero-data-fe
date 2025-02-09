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


APT_TRAFFIC_TYPE = {0: "VFR", 1: "IFR"}

# Services
APT_FUEL_TYPES = {
    0: "Super PLUS",
    1: "AVGAS",
    2: "Jet A",
    3: "Jet A1",
    4: "Jet B",
    5: "Diesel",
    6: "AVGAS UL91",
}

APT_GLIDER_TOWING = {
    0: "Self Launch",
    1: "Winch",
    2: "Tow",
    3: "Auto Tow",
    4: "Bungee",
    5: "Gravity Powered",
}

APT_HANDLING_FACILITIES = {
    0: "Cargo Handling",
    1: "De-Icing",
    2: "Maintenance",
    3: "Security",
    4: "Shelter",
}

APT_PASSANGER_FACILITIES = {
    0: "Bank Office",
    1: "Post Office",
    2: "Customs",
    3: "Lodging",
    4: "Medical Facility",
    5: "Restaurant",
    6: "Sanitation",
    7: "Transportation",
    8: "Laundry Service",
    9: "Camping",
}

# Frequencies
APT_FREQUENCY_TYPE = {
    0: "Approach",
    1: "APRON",
    2: "Arrival",
    3: "Center",
    4: "CTAF",
    5: "Delivery",
    6: "Departure",
    7: "FIS",
    8: "Gliding",
    9: "Ground",
    10: "Information",
    11: "Multicom",
    12: "Unicom",
    13: "Radar",
    14: "Tower",
    15: "ATIS",
    16: "Radio",
    17: "Other",
    18: "AIRMET",
    19: "AWOS",
    20: "Lights",
    21: "VOLMET",
    22: "AFIS",
}

RADIO_TYPE_PRIORITY = {
    8: 0,
    14: 1,
    10: 2,
    16: 3,
    4: 4,
    12: 5,
    11: 6,
    3: 7,
    13: 8,
    7: 9,
    0: 10,
    22: 11,
    2: 12,
    6: 13,
    9: 14,
    1: 15,
    17: 16,
    21: 17,
    19: 18,
    15: 19,
    18: 20,
    5: 21,
    20: 22,
}

APT_FREQUENCY_UNIT = {1: "kHz", 2: "MHz"}

# Runways
APT_RUNWAY_OPERATIONS = {
    0: "Active",
    1: "Temporarily Closed",
    2: "Closed",
}

APT_RUNWAY_TURN_DIRECTION = {
    0: "Right",
    1: "Left",
    2: "Both",
}

APT_RUNWAY_SURFACE_COMPOSITION = {
    0: "Asphalt",
    1: "Concrete",
    2: "Grass",
    3: "Sand",
    4: "Water",
    5: "Bituminous tar or asphalt",
    6: "Brick",
    7: "Macadam or tarmac surface consisting of water-bound crushed rock",
    8: "Stone",
    9: "Coral",
    10: "Clay",
    11: "Laterite - a high iron clay formed in tropical areas",
    12: "Gravel",
    13: "Earth",
    14: "Ice",
    15: "Snow",
    16: "Protective laminate usually made of rubber",
    17: "Metal",
    18: "Landing mat portable system usually made of aluminium",
    19: "Pierced steel planking",
    20: "Wood",
    21: "Non Bituminous mix",
    22: "Unknown",
}

APT_RUNWAY_CONDITION = {
    0: "Good",
    1: "Fair",
    2: "Poor",
    3: "Unsafe",
    4: "Deformed",
    5: "Unknown",
}

APT_RUNWAY_EXCLUSIVE_AIRCRAFT_TYPE = {
    0: "Single Engine Piston",
    1: "Single Engine Turbine",
    2: "Multi Engine Piston",
    3: "Multi Engine",
    4: "High Performance Aircraft",
    5: "Touring Motor Glider",
    6: "Experimental",
    7: "Very Light Aircraft",
    8: "Glider",
    9: "Light Sport Aircraft",
    10: "Ultra Light Aircraft",
    11: "Hang Glider",
    12: "Paraglider",
    13: "Balloon",
}

APT_RUNWAY_LIGHTING_SYSTEM = {
    0: "Runway End Identifier Lights",
    1: "Runway End Lights",
    2: "Runway Edge Lights",
    3: "Runway Center line Lighting System",
    4: "Touchdown Zone Lights",
    5: "Taxiway Centerline Lead Off Lights",
    6: "Taxiway Centerline Lead On Lights",
    7: "Land And Hold Short Lights",
    8: "Approach Lighting System",
    9: "Threshold Lights",
}

APT_RUNWAY_VISUAL_APPROACH_AIDS = {
    0: "Visual Approach Slope Indicator",
    1: "Precision Approach Path Indicator",
    2: "Tri-Color Visual Approach Slope Indicator",
    3: "Pulsating Visual Approach Slope Indicator",
    4: "Alignment Of Elements System",
}

APT_RUNWAY_INSTRUMENT_APPROACH_AIDS_TYPE = {
    0: "ILS - Instrument Landing System",
    1: "LOC - Localizer Approach",
    2: "LDA - Localizer Type Directional Aid Approach",
    3: "L- Locator (Compass Locator)",
    4: "DME - Distance Measuring Equipment",
    5: "GP - Glide Path",
}
