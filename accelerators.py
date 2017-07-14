import gapi

WORKSHEET_NAME = "Accelerators"
ORG_COLUMN = 1
PROGRAM_COLUMN = 3
CITY_COLUMN = 9
STATE_COLUMN = 8
COUNTRY_COLUMN = 17

GEOLOCATION_COLUMN = 14
GEOLOCATION_COLUMN_TITLE = "Geo Coordinates"

global_latlngs = []
my_worksheet = None

def get_location(record):
    return "%s, %s, %s" % (record[CITY_COLUMN], record[STATE_COLUMN], record[COUNTRY_COLUMN])

def set_geolocations(global_latlngs, worksheet):
    latlngs = global_latlngs
    my_worksheet = worksheet

accelerators = sh.worksheet(accelerators.WORKSHEET_NAME)
orgs = accelerators.col_values(accelerators.ORG_COLUMN)[1:]
progs = accelerators.col_values(accelerators.PROGRAM_COLUMN)[1:]
locs = accelerators.col_values(accelerators.get_location())[1:]


# Does the worksheet already have a geo coordinates column?
geocoord_title = accelerators.col_values(accelerators.GEOLOACTION_COLUMN)[0]

if geocoord_title and (geocoord_title != ACCELERATOR_GEOLOCATION_COLUMN_TITLE):
    print("Found '%s' where '%s' is supposed to be. Quitting." % (geocoord_title, ACCELERATOR_GEOLOCATION_COLUMN_TITLE))
    sys.exit()

if not geocoord_title:
    accelerators.update_cell(1, ACCELERATOR_GEOLOCATION_COLUMN, ACCELERATOR_GEOLOCATION_COLUMN_TITLE)
    print("Created '%s' column" % ACCELERATOR_GEOLOCATION_COLUMN_TITLE)


# @todo this should be get_lat_lng(results) instead, and the caller should subsequently call jiggle() and update the cell.
def process_results(results):
    print(results["results"][0]["name"])
    # @todo formatted_address is useful, and should be added as a new column
    print(results["results"][0]["formatted_address"])
    print(results["results"][0]["place_id"])

    lat = results["results"][0]["geometry"]["location"]["lat"]
    lng = results["results"][0]["geometry"]["location"]["lng"]

    print("%f, %f" % (lat, lng))

    if (lat, lng) in global_latlngs:
        print("We already have (%f, %f). Jiggling..." % (lat, lng))
        (lat, lng) = gapi.jiggle(lat, lng)
        print("... Now it's (%f, %f)" % (lat, lng))

    # write to the row offset +2; one because rows are 1-indexed, and one because the title is row 1
    accelerators.update_cell(i+2, ACCELERATOR_GEOLOCATION_COLUMN, "%f, %f" % (lat, lng))
    global_latlngs.append((lat, lng))

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

    query = "%s, %s" % (identifier.strip(), program_location)
    print("\nLooking up %s" % query)

    query_results = gapi.query_location(PLACE_API_KEY, query)

    if query_results["status"] == "OK":
        process_results(query_results)
        worksheet_updated = True

    elif query_results["status"] == "ZERO_RESULTS":
        # fall back to only the program location
        print("Not found. Trying %s instead" % program_location)
        query_results = gapi.query_location(PLACE_API_KEY, program_location)
        if query_results["status"] == "OK":
            process_results(query_results)
            worksheet_updated = True

    elif query_results["status"] == "OVER_QUERY_LIMIT":
        print(query_results["status"])
        sys.exit()

    time.sleep(3)





    return latlngs

