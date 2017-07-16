import logging
from logging.config import fileConfig
import gspread
import json
import sys
import datetime
import dateutil.parser
import time
from oauth2client.service_account import ServiceAccountCredentials

import update_file
import accelerators

# @todo import food_incubators
# @todo import university_extension_programs
# @todo import tech_incubators
# @todo import pilot_plants
# @todo import pilot_plants
# @todo import educational_opportunities
# @todo import vdos
# @todo import networks_coworking
# @todo import prizes
# @todo import contract_research_orgs
# @todo import conferences_expos_pitches
# @todo import other
# @todo import co_manufacturers
# @todo import business_incubators
# @todo import corp_food_incubators
# @todo import grants

DOCUMENT_TITLE = "Copy of Global Map of Accelerators and Incubators.xlsx"

# use credentials to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(credentials)

PLACE_API_KEY = None
worksheet_updated = False
global_latlngs = []

# Arbitrary time in the far past
default_datetime = datetime.datetime(1984, 1, 24, 17, 0, 0, 0, tzinfo=datetime.timezone.utc)


def main():
    # We're storing the Google Place API key in the gspread credentials file for convenience.
    try:
        with open('client_secret.json') as config:
            PLACE_API_KEY = json.load(config)["api_key"]
    except IOError as error:
        print("There was a problem reading client_secret.json: %s" % str(error))
        sys.exit()

    # load the last updated timestamp record
    last_updated_datetime = update_file.get_last_update(default_datetime)

    # Find a workbook by name and open the first sheet
    sheet = client.open(DOCUMENT_TITLE)

    print("Got %s, last updated at %s" % (DOCUMENT_TITLE, sheet.updated))
    print("Last update on record was at %s" % last_updated_datetime)
    sheet_updated_datetime = dateutil.parser.parse(sheet.updated)
    if sheet_updated_datetime <= last_updated_datetime:
        print("Nothing to do.")
        sys.exit()

    # models = [accelerators, university_extension_programs, tech_incubators, pilot_plants,
    # pilot_plants, educational_opportunities, vdos, networks_coworking, prizes,
    # contract_research_orgs, conferences_expos_pitches, other, co_manufacturers, business_incubators,
    # corp_food_incubators, grants]

    worksheets = [accelerators]

    # Pass the Sheet object to each model to process. If a worksheet has performed an update it will return True
    for worksheet in worksheets:
        if worksheet.process(sheet, PLACE_API_KEY):
            global_latlngs += set(global_latlngs) - set(model.get_latlngs())
            worksheet_updated = True
        time.sleep(2)

    if worksheet_updated:
        # see https://stackoverflow.com/a/8556555/364050
        now_timestamp = datetime.datetime.utcnow().isoformat("T") + "Z"
        update_file.set_last_update(now_timestamp)

if __name__ == '__main__':
    fileConfig('logging_config.ini')
    now_timestamp = datetime.datetime.utcnow().isoformat("T") + "Z"
    logger = logging.getLogger()
    logger.info('Started at %s' % now_timestamp)
    main()

