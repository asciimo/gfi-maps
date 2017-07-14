import gspread
import time
import json
import sys
import datetime
import dateutil.parser
from oauth2client.service_account import ServiceAccountCredentials

import gapi
import update_file

import accelerators

# @todo move all sheet CONFIGURATION_VALUES into a file
DOCUMENT_TITLE = "Copy of Global Map of Accelerators and Incubators.xlsx"

# use credentials to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

PLACE_API_KEY = None
worksheet_updated = False

# Arbitrary time in the far past
default_datetime = datetime.datetime(1984, 1, 24, 17, 0, 0, 0, tzinfo=datetime.timezone.utc)

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
sh = client.open(DOCUMENT_TITLE)

print("Got %s, last updated at %s" % (DOCUMENT_TITLE, sh.updated))
print("Last update on record was at %s" % last_updated_datetime)
sheet_updated_datetime = dateutil.parser.parse(sh.updated)
if sheet_updated_datetime <= last_updated_datetime:
    print("Nothing to do.")
    sys.exit()

# Helps us identify duplicate lat/lngs for jiggling
global_latlngs = []

models = [accelerators]

for model in models:
    global_latlngs = model.set_geolocations(sh, global_latlngs)
    # Will the global_latlngs in this scope be mutated by model.set_geolocations?
    if (model.was_updated):
        worksheet_updated = True

if worksheet_updated:
    # see https://stackoverflow.com/a/8556555/364050
    now_timestamp = datetime.datetime.utcnow().isoformat("T") + "Z"
    update_file.set_last_update(now_timestamp)
