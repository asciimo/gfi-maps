import logging
import gapi
import sys

logger = logging.getLogger()

WORKSHEET_NAME = "Accelerators"

INDEX_COLUMN = 2  # Program
ORG_COLUMN = 0
CITY_COLUMN = 8
STATE_COLUMN = 7
COUNTRY_COLUMN = 6

GEOLOCATION_COLUMN = 16
GEOLOCATION_COLUMN_TITLE = "Geo Coordinates"


def get_lat_lngs():
    return latlngs


def has_location_values(record):
    return record[CITY_COLUMN] != "" and record[STATE_COLUMN] != "" and record[COUNTRY_COLUMN] != ""


def get_location(record):
    return ",".join((record[CITY_COLUMN], record[STATE_COLUMN], record[COUNTRY_COLUMN]))


def get_lat_lng(results):

    lat = results["results"][0]["geometry"]["location"]["lat"]
    lng = results["results"][0]["geometry"]["location"]["lng"]

    logger.debug("%f, %f" % (lat, lng))

    return lat, lng


def set_geolocation_column(worksheet):
    # Does the worksheet already have a geo coordinates column?
    geocoord_title = worksheet.col_values(GEOLOCATION_COLUMN+1)[0]

    if geocoord_title and (geocoord_title != GEOLOCATION_COLUMN_TITLE):
        logger.debug("Found '%s' where '%s' is supposed to be. Quitting." % (geocoord_title, GEOLOCATION_COLUMN_TITLE))
        sys.exit()

    if not geocoord_title:
        worksheet.update_cell(1, GEOLOCATION_COLUMN+1, GEOLOCATION_COLUMN_TITLE)
        logger.debug("Created '%s' column" % GEOLOCATION_COLUMN_TITLE)

    return worksheet


def get_location_identifier(record):
    # @todo each module gets one of these, as the module knows the worksheet format
    if record[ORG_COLUMN] != 'N/A' and record[ORG_COLUMN] != '':
        return record[ORG_COLUMN]

    return record[INDEX_COLUMN]


def process(sheet, google_places_api_key):

    updated = False

    latlngs = []

    logger.debug("Loading worksheet %s" % WORKSHEET_NAME)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    indexes = worksheet.col_values(INDEX_COLUMN)[1:]

    if len(indexes) < 1:
        logger.debug("%s: index column %d appears to be empty." % (WORKSHEET_NAME, INDEX_COLUMN))
        return False

    worksheet = set_geolocation_column(worksheet)

    # @todo this iteration is VERBOSE. And probably generic. Abstract it.
    for i in range(2, len(indexes)):  # row access is 1-indexed, and the first row is the title row

        record = worksheet.row_values(i)

        if not has_location_values(record):
            continue

        identifier = get_location_identifier(record)
        location = get_location(record)

        query = "%s, %s" % (identifier.strip(), location)
        logger.debug("Querying for %s..." % query)

        results = gapi.query_location(google_places_api_key, query)

        # @todo DRY
        if results["status"] == "OK":
            logger.debug(results["results"][0]["name"])
            logger.debug(results["results"][0]["formatted_address"])
            logger.debug(results["results"][0]["place_id"])

            (lat, lng) = get_lat_lng(results)

            # write to the row offset +2; one because rows are 1-indexed, and one because the title is row 1
            worksheet.update_cell(i+2, GEOLOCATION_COLUMN, "%f, %f" % (lat, lng))
            latlngs.append((lat, lng))
            updated = True

        elif results["status"] == "ZERO_RESULTS":
            # fall back to only the program location
            logger.debug("Not found. Trying %s instead" % location)
            results = gapi.query_location(google_places_api_key, location)
            if results["status"] == "OK":
                (lat, lng) = get_lat_lng(results)
                if (lat, lng) in latlngs:
                    logger.debug("We already have (%f, %f). Jiggling..." % (lat, lng))
                    (lat, lng) = gapi.jiggle(lat, lng)
                    logger.debug("... Now it's (%f, %f)" % (lat, lng))
                updated = True

        elif results["status"] == "OVER_QUERY_LIMIT":
            logger.debug("%s. Quitting." % results["status"])
            sys.exit()

    return updated

