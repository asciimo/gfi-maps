"""
A module for interacting with the
"""
import requests
import random

PLACE_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def query_location(google_places_api_key, query):
    """
    :param key: Google Places API key
    :param query: The location to search e.g. "Some Company, Trenton, NJ, United States"
    :return:
    """
    payload = {
        'key': google_places_api_key,
        'query': query
    }
    request = requests.get(PLACE_API_URL, params=payload)
    return request.json()


def jiggle(lat, lng):
    new_lat = lat + round(random.uniform(.01, -.01), 5)
    new_lng = lng + round(random.uniform(.01, -.01), 5)
    return new_lat, new_lng


