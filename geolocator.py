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

from accelerators import Accelerators
from food_incubators import FoodIncubators
from university_extension_programs import UniversityExtensionPrograms
from tech_incubators import TechIncubators
from pilot_plants import PilotPlants
from educational_opportunities import EducationalOpportunities
from vdos import Vdos
from networks_coworking import NetworksCoworking
from prizes import Prizes
from contract_research_orgs import ContractResearchOrgs
from conferences_expos_pitches import ConferencesExposPitches
from other import Other
from co_manufacturers import CoManufacturers
from business_incubators import BusinessIncubators
from corp_food_incubators import CorpFoodIncubators
from grants import Grants

DOCUMENT_TITLE = "Copy of Global Map of Accelerators and Incubators.xlsx"
PLACES_REQUEST_DELAY = 2

# use credentials to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(credentials)


# Arbitrary time in the far past
default_datetime = datetime.datetime(1984, 1, 24, 17, 0, 0, 0, tzinfo=datetime.timezone.utc)


def main():
    google_places_api_key = None
    lat_lngs = []
    worksheet_updated = False

    # We're storing the Google Place API key in the gspread credentials file for convenience.
    try:
        with open('client_secret.json') as config:
            google_places_api_key = json.load(config)["google_places_api_key"]
    except IOError as error:
        logger.error("There was a problem reading client_secret.json: %s" % str(error))
        sys.exit()

    # load the last updated timestamp record
    last_updated_datetime = update_file.get_last_update(default_datetime)

    # Find a workbook by name and open the first sheet
    sheet = client.open(DOCUMENT_TITLE)

    logger.debug("Got %s, last updated at %s" % (DOCUMENT_TITLE, sheet.updated))
    logger.debug("Last update on record was at %s" % last_updated_datetime)
    sheet_updated_datetime = dateutil.parser.parse(sheet.updated)
    if sheet_updated_datetime <= last_updated_datetime:
        logger.debug("Nothing to do.")
        sys.exit()

    # models = [Accelerators, FoodIncubators, UniversityExtensionPrograms, TechIncubators, PilotPlants,
    # EducationalOpportunities, Vdos, NetworksCoworking, Prizes, ContractResearchOrgs, ConferencesExposPitches, Other,
    # CoManufacturers, BusinessIncubators, CorpFoodIncubators, Grants]
    models = [CoManufacturers]

    # Pass the Sheet object to each model to process. If a worksheet has performed an update it will return True
    for Model in models:
        ws = Model(sheet)
        (worksheet_updated, worksheet_lat_lngs) = ws.process(sheet, google_places_api_key, lat_lngs)
        if worksheet_updated:
            lat_lngs += set(lat_lngs) - set(worksheet_lat_lngs)
        time.sleep(PLACES_REQUEST_DELAY)

    if worksheet_updated:
        # see https://stackoverflow.com/a/8556555/364050
        now_timestamp = datetime.datetime.utcnow().isoformat("T") + "Z"
        update_file.set_last_update(now_timestamp)

if __name__ == '__main__':
    fileConfig('logging_config.ini')
    start_timestamp = datetime.datetime.utcnow().isoformat("T") + "Z"
    logger = logging.getLogger()
    logger.info('Started at %s' % start_timestamp)
    main()

