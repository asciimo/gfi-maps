"""
A module for interacting with the
"""
import requests

PLACE_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def query_location(key, query):
    """
    :param key: Google Places API key
    :param query: The location to search e.g. "Some Company, Trenton, NJ, United States"
    :return:
    """
    payload = {
        'key': key,
        'query': query
    }
    request = requests.get(PLACE_API_URL, params=payload)
    return request.json()
