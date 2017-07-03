import gspread
import requests
import time
from oauth2client.service_account import ServiceAccountCredentials

DOCUMENT_TITLE = "Copy of Global Map of Accelerators and Incubators.xlsx"

ACCELERATOR_WORKSHEET = "Accelerators"
ACCELERATOR_ORG_COLUMN = 1
ACCELERATOR_PROGRAM_COLUMN = 3
ACCELERATOR_LOCATION_COLUMN = 6

GOOGLE_API_KEY = "KEY"

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

PLACE_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# Find a workbook by name and open the first sheet
sh = client.open(DOCUMENT_TITLE)

accelerators = sh.worksheet(ACCELERATOR_WORKSHEET)
orgs = accelerators.col_values(ACCELERATOR_ORG_COLUMN)[1:]
progs = accelerators.col_values(ACCELERATOR_PROGRAM_COLUMN)[1:]
locs = accelerators.col_values(ACCELERATOR_LOCATION_COLUMN)[1:]

for i in range(len(orgs)):

    identifier = None

    if 'Virtual' in locs[i] or locs[i] == '':
        continue
    elif orgs[i] == 'N/A' or orgs[i] == '':
        # Try to use the program name instead
        if progs[i] == '':
            continue
        else:
            identifier = progs[i]
    else:
        identifier = orgs[i]

    payload = {
        'key': GOOGLE_API_KEY,
        'query': "%s,%s" % (identifier.strip(), locs[i].strip())
    }
    request = requests.get(PLACE_API_URL, params=payload)
    response = request.json()

    if response["status"] == "OK":
        print(identifier)
        print(response["results"][0]["formatted_address"])
        print(response["results"][0]["place_id"])
        print(response["results"][0]["geometry"]["location"]["lat"])
        print(response["results"][0]["geometry"]["location"]["lng"])

    time.sleep(5)

# the "status" key will be OK, or ZERO_RESULTS
# @todo if we get OVER_QUERY_LIMIT we should stop querying for the day
# @todo if the lat/lng is the same as any other place, "jiggle" it a tiny bit

