import logging
import gapi
import sys


class Worksheet(object):

    geolocation_column_title = "Geo Coordinates"

    def __init__(self, spreadsheet):

        self.spreadsheet = spreadsheet
        self.worksheet = None
        self.logger = logging.getLogger()

    def has_location_values(self, record):
        """
        A record must at least a city,state pair or a country value.
        :param record: Array of record values
        :return:
        """
        return (record[self.city_column] != "" and record[self.state_column] != "") or record[self.country_column] != ""

    def get_location(self, record):
        location_fields = (record[self.city_column], record[self.state_column], record[self.country_column])
        return ",".join(filter(None, location_fields))

    def get_lat_lng(self, results):
        lat = results["results"][0]["geometry"]["location"]["lat"]
        lng = results["results"][0]["geometry"]["location"]["lng"]

        self.logger.debug("%f, %f" % (lat, lng))

        return lat, lng

    def set_geolocation_column(self):
        # Does the worksheet already have a geo coordinates column?
        geocoord_title = self.worksheet.col_values(self.geolocation_column + 1)[0]

        if geocoord_title and (geocoord_title != self.geolocation_column_title):
            self.logger.debug(
                "Found '%s' where '%s' is supposed to be. Quitting." % (geocoord_title, self.geolocation_column_title))
            sys.exit()

        if not geocoord_title:
            self.worksheet.update_cell(1, self.geolocation_column + 1, self.geolocation_column_title)
            self.logger.debug("Created '%s' column" % self.geolocation_column_title)

    def get_location_identifier(self, record):
        """
        The identifier is the company, organization, or program name. This is what gets submitted to Google
        as part of the address query to determine the correct Place

        :param record: Worksheet row
        :return: the best available location identifier
        """
        if record[self.org_column] != 'N/A' and record[self.org_column] != '':
            return record[self.org_column]

        return record[self.index_column]

    def update_record(self, index, lat_lngs, results):
        """
        Sets the latitude and longitude in the geo coordinates field for the record

        :param index: the row to update in the worksheet
        :param lat_lngs: list of all latitude and longitude pairs encountered thus far
        :param results: Google Place API results
        :return: the latitude and longitude pa
        """
        self.logger.debug(results["results"][0]["name"])
        self.logger.debug(results["results"][0]["formatted_address"])
        self.logger.debug(results["results"][0]["place_id"])

        (lat, lng) = self.get_lat_lng(results)
        if (lat, lng) in lat_lngs:
            self.logger.debug("We already have (%f, %f). Jiggling..." % (lat, lng))
            (lat, lng) = gapi.jiggle(lat, lng)
            self.logger.debug("... Now it's (%f, %f)" % (lat, lng))

        # write to the row offset +2; +1 because rows are 1-indexed, and +1 because the title is row 1
        self.worksheet.update_cell(index, self.geolocation_column + 1, "%f, %f" % (lat, lng))
        return lat, lng

    def process(self, sheet, google_places_api_key, lat_lngs):
        updated = False

        self.logger.debug("Loading worksheet %s" % self.name)
        self.worksheet = sheet.worksheet(self.name)

        indexes = self.worksheet.col_values(self.index_column + 1)[1:]

        if len(indexes) < 1:
            self.logger.debug("%s: index column %d appears to be empty." % (self.name, self.index_column))
            return False

        self.set_geolocation_column()

        for i in range(2, len(indexes)):  # row access is 1-indexed, and the first row is the title row

            record = self.worksheet.row_values(i)

            # An empty index value signifies the end of worksheet
            if not record[self.index_column]:
                break

            if not self.has_location_values(record):
                continue

            identifier = self.get_location_identifier(record)
            location = self.get_location(record)

            query = "%s, %s" % (identifier.strip(), location)
            self.logger.debug("Querying for %s..." % query)

            results = gapi.query_location(google_places_api_key, query)

            if results["status"] == "OK":
                lat_lngs.append(self.update_record(i, lat_lngs, results))
                updated = True

            elif results["status"] == "ZERO_RESULTS":
                # fall back to only the program location
                self.logger.debug("Not found. Trying %s instead" % location)
                results = gapi.query_location(google_places_api_key, location)
                if results["status"] == "OK":
                    lat_lngs.append(self.update_record(i, lat_lngs, results))
                    updated = True

            elif results["status"] == "OVER_QUERY_LIMIT":
                self.logger.debug("%s. Quitting." % results["status"])
                sys.exit()

        return updated, lat_lngs
