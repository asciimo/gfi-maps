import gspread
import requests
import time
import json
import sys
import random
import datetime
import dateutil.parser
from oauth2client.service_account import ServiceAccountCredentials

# @todo move all CONFIGURATION_VALUES into a file
DOCUMENT_TITLE = "Copy of Global Map of Accelerators and Incubators.xlsx"

ACCELERATOR_WORKSHEET = "Accelerators"
ACCELERATOR_ORG_COLUMN = 1
ACCELERATOR_PROGRAM_COLUMN = 3
ACCELERATOR_LOCATION_COLUMN = 6

ACCELERATOR_GEOLOCATION_COLUMN = 14
ACCELERATOR_GEOLOCATION_COLUMN_TITLE = "Geo Coordinates"


# use credentials to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

PLACE_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

PLACE_API_KEY = None
worksheet_updated = False

# Arbitrary time in the far past
last_updated_datetime = datetime.datetime(1984, 1, 24, 17, 0, 0, 0, tzinfo=datetime.timezone.utc)

# We're storing the Google Place API key in the gspread credentials file for convenience.
try:
    with open('client_secret.json') as config:
        PLACE_API_KEY = json.load(config)["api_key"]
except IOError as error:
    print("There was a problem reading client_secret.json: %s" % str(error))
    sys.exit()

# load the last updated timestamp record
try:
    with open('updated.dat', 'r+') as timestamp:
        last_updated = timestamp.read().strip()
        if last_updated:
            try:
                last_updated_datetime = dateutil.parser.parse(last_updated)
            except ValueError as error:
                print("Can't parse %s into datetime: %s" % (last_updated, str(error)))
except IOError as error:
    print("There was a problem reading updated.dat: %s" % str(error))

# Find a workbook by name and open the first sheet
sh = client.open(DOCUMENT_TITLE)

print("Got %s, last updated at %s" % (DOCUMENT_TITLE, sh.updated))
print("Last update on record was at %s" % last_updated_datetime)
sheet_updated = dateutil.parser.parse(sh.updated)
if sheet_updated <= last_updated_datetime:
    print("Nothing to do.")
    sys.exit()

# @todo each worksheet type needs its own configuration
accelerators = sh.worksheet(ACCELERATOR_WORKSHEET)
orgs = accelerators.col_values(ACCELERATOR_ORG_COLUMN)[1:]
progs = accelerators.col_values(ACCELERATOR_PROGRAM_COLUMN)[1:]
locs = accelerators.col_values(ACCELERATOR_LOCATION_COLUMN)[1:]

# Does the worksheet already have a geo coordinates column?
geocoord_title = accelerators.col_values(ACCELERATOR_GEOLOCATION_COLUMN)[0]

if geocoord_title and (geocoord_title != ACCELERATOR_GEOLOCATION_COLUMN_TITLE):
    print("Found '%s' where '%s' is supposed to be. Quitting." % (geocoord_title, ACCELERATOR_GEOLOCATION_COLUMN_TITLE))
    sys.exit()

if not geocoord_title:
    accelerators.update_cell(1, ACCELERATOR_GEOLOCATION_COLUMN, ACCELERATOR_GEOLOCATION_COLUMN_TITLE)
    print("Created '%s' column" % ACCELERATOR_GEOLOCATION_COLUMN_TITLE)

# Helps us identify duplicate lat/lngs for jiggling
all_latlngs = []


def jiggle(lat, lng):
    new_lat = lat + round(random.uniform(.01, -.01), 5)
    new_lng = lng + round(random.uniform(.01, -.01), 5)
    return new_lat, new_lng


def process_results(results):
    print(results["results"][0]["name"])
    # @todo formatted_address is useful, and should be added as a new column
    print(results["results"][0]["formatted_address"])
    print(results["results"][0]["place_id"])

    lat = results["results"][0]["geometry"]["location"]["lat"]
    lng = results["results"][0]["geometry"]["location"]["lng"]

    print("%f, %f" % (lat, lng))

    if (lat, lng) in all_latlngs:
        print("We already have (%f, %f). Jiggling..." % (lat, lng))
        (lat, lng) = jiggle(lat, lng)
        print("... Now it's (%f, %f)" % (lat, lng))

    # write to the row offset +2; one because rows are 1-indexed, and one because the title is row 1
    accelerators.update_cell(i+2, ACCELERATOR_GEOLOCATION_COLUMN, "%f, %f" % (lat, lng))
    all_latlngs.append((lat, lng))


def query_location(query):
    payload = {
        'key': PLACE_API_KEY,
        'query': query
    }
    request = requests.get(PLACE_API_URL, params=payload)
    return request.json()


for i in range(len(orgs)):

    identifier = None

    # The place identifier in order of preference: organization, program, program location
    if 'Virtual' in locs[i] or locs[i] == '':
        continue
    elif orgs[i] == 'N/A' or orgs[i] == '':
        # Try to use the program name instead. (There's always a program.)
        if progs[i] == '':
            continue
        else:
            identifier = progs[i]
    else:
        identifier = orgs[i]

    program_location = locs[i].strip()
    query_results = query_location("%s,%s" % (identifier.strip(), program_location))

    if query_results["status"] == "OK":
        process_results(query_results)
        worksheet_updated = True

    elif query_results["status"] == "ZERO_RESULTS":
        # fall back to only the program location
        query_results = query_location(program_location)
        if query_results["status"] == "OK":
            process_results(query_results)
            worksheet_updated = True

    elif query_results["status"] == "OVER_QUERY_LIMIT":
        print(query_results["status"])
        sys.exit()

    time.sleep(5)

if worksheet_updated:
    timestamp.write(sh.updated)
