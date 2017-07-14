WORKSHEET_NAME = "Food Incubators"
ORG_COLUMN = 1
PROGRAM_COLUMN = 3
CITY_COLUMN = 7
STATE_COLUMN = 6
COUNTRY_COLUMN = 5

GEOLOCATION_COLUMN = 10
GEOLOCATION_COLUMN_TITLE = "Geo Coordinates"


def get_location(record):
    return "%s, %s, %s" % (record[CITY_COLUMN], record[STATE_COLUMN], record[COUNTRY_COLUMN])

