import base64
import csv
import hashlib
import json
import os.path
from functools import cached_property
from typing import Generator, TypedDict

import requests

from common import DATA_DIR, JSON, SRC_DIR


class FoodNutrientDict(TypedDict):
    """
    Example of a food nutrient dictionary:
    {
        "number": "268",
        "name": "Energy",
        "amount": 1530.0,
        "unitName": "kJ",
        "derivationCode": "NC",
        "derivationDescription": "Calculated"
    }
    """

    number: str
    name: str
    amount: float
    unitName: str
    derivationCode: str
    derivationDescription: str


class FoodDict(TypedDict):
    """
    Example of a food dictionary:
    {
        "fdcId": 789890,
        "description": "Flour, wheat, all-purpose, enriched, bleached",
        "dataType": "Foundation",
        "publicationDate": "2020-04-01",
        "ndbNumber": "20081",
        "foodNutrients": [ ... ]
    }
    """

    fdcId: int
    description: str
    dataType: str
    publicationDate: str
    ndbNumber: str
    foodNutrients: list[FoodNutrientDict]


class FoodDataCentral:
    """
    A class to interact with the USDA Food Data Central API

    More info on: https://fdc.nal.usda.gov/api-guide.html
    API docs on: https://app.swaggerhub.com/apis/fdcnal/food-data_central_api/1.0.1#/
    """

    BASE_URL = 'https://api.nal.usda.gov/fdc'

    @cached_property
    def api_key(self) -> str:
        """
        Get the API key from the secrets file, or return a demo key if no proper API key has been defined
        """

        default_demo_key = 'DEMO_KEY'

        secrets_file = os.path.join(SRC_DIR, 'secrets.json')
        if not os.path.exists(secrets_file):
            return default_demo_key

        try:
            with open(secrets_file) as f:
                secrets = json.load(f)
        except json.JSONDecodeError:
            return default_demo_key

        try:
            return secrets['FOOD_DATA_CENTRAL_API_KEY']
        except KeyError:
            return default_demo_key

    def food_list(self) -> Generator[FoodDict, None, None]:
        url = 'v1/foods/list'
        params = {
            'dataType': 'Foundation',
        }
        yield from self._make_paginated_get_call(url, params)

    def _make_paginated_get_call(self, url: str, params: dict = None) -> list[dict]:
        """
        Make a paginated GET call to the API
        """

        params = params or {}
        params['pageSize'] = 50
        page = 1
        while True:
            params['pageNumber'] = page
            data = self._make_get_call(url, params)
            if not data:
                break
            yield from data
            page += 1

    def _make_get_call(self, url: str, params: dict = None) -> list[dict]:
        """
        Make a GET call to the API
        """

        url = f'{self.BASE_URL}/{url}'
        params = params or {}
        url_params = '&'.join([f'{key}={value}' for key, value in params.items()])
        if url_params:
            url = f'{url}?{url_params}'

        # Check if the response is already in the cache
        data = self._get_response_from_cache(url)
        if data is None:
            # If the response is not in the cache yet, get the response from the API and cache it
            response = requests.get(url, params={'api_key': self.api_key})
            response.raise_for_status()
            data = response.json()
            self._add_response_to_cache(url, data)

            ratelimit_remaining = response.headers.get('X-Ratelimit-Remaining')
            ratelimit_limit = response.headers.get('X-Ratelimit-Limit')
            print(f'Added response from {url} to cache. Remaining calls: {ratelimit_remaining}/{ratelimit_limit}')

        return data

    @staticmethod
    def hash_url_to_alphanumeric(url: str) -> str:
        """
        Hash a URL to an alphanumeric string

        >>> FoodDataCentral.hash_url_to_alphanumeric('https://example.com')
        'EAaArVRs5qV39C9S3zO0z9ynVoWeZkuNfeMpsVDQnOk'
        """

        # Step 1: Hash the URL using SHA-256
        url_hash = hashlib.sha256(url.encode('utf-8')).digest()

        # Step 2: Encode the hash using base64
        base64_encoded = base64.urlsafe_b64encode(url_hash).decode('utf-8')

        # Step 3: Remove any '=' characters used as padding in base64 encoding
        alphanumeric_hash = base64_encoded.rstrip('=')

        return alphanumeric_hash

    def _get_response_from_cache(self, url: str) -> JSON:
        """
        Get the cached response for a given URL
        """

        url_hash = self.hash_url_to_alphanumeric(url)
        cache_file = os.path.join(DATA_DIR, 'fdc_cache', f'{url_hash}.json')
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                return json.load(f)
        return None

    def _add_response_to_cache(self, url: str, data: JSON):
        """
        Add a response to the cache
        """

        url_hash = self.hash_url_to_alphanumeric(url)
        cache_file = os.path.join(DATA_DIR, 'fdc_cache', f'{url_hash}.json')
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)


class CsvGenerator:
    """
    Class to convert FDC API data into CSV format
    """

    FDC_DATA_DIR = os.path.join(DATA_DIR, 'fdc_data')

    def __init__(self):
        self.fdc = FoodDataCentral()

    @cached_property
    def food_list(self) -> list[FoodDict]:
        return list(self.fdc.food_list())

    def generate_nutrient_definitions_csv(self):
        result = {
            nutrient['number']: {
                'number': nutrient['number'],
                'name': nutrient['name'],
                'unitName': nutrient['unitName'],
                'derivationCode': nutrient.get('derivationCode'),
                'derivationDescription': nutrient.get('derivationDescription'),
            }
            for food in self.food_list
            for nutrient in food['foodNutrients']
        }
        nutrients = sorted(result.values(), key=lambda x: x['number'])

        nutrients_csv = os.path.join(self.FDC_DATA_DIR, 'nutrient_definitions.csv')
        with open(nutrients_csv, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=nutrients[0].keys(), delimiter=';')
            writer.writeheader()
            writer.writerows(nutrients)

    def generate_food_nutrients_csv(self):
        result = {}
        for food in self.food_list:
            line = {
                'fdcId': food['fdcId'],
                'description': food['description'],
                'dataType': food['dataType'],
                'publicationDate': food['publicationDate'],
                'ndbNumber': food['ndbNumber'],
            }
            for nutrient in food['foodNutrients']:
                # Some food nutrients have no amount specified. We assume 0 for them
                line[nutrient['number']] = nutrient.get('amount', 0)
            result[food['fdcId']] = line
        food_nutrients = sorted(result.values(), key=lambda x: x['fdcId'])

        food_nutrients_csv = os.path.join(self.FDC_DATA_DIR, 'food_nutrients.csv')
        # Concatenate all keys from all dictionaries into a set
        food_field_names = ['fdcId', 'description', 'dataType', 'publicationDate', 'ndbNumber']
        nutrient_field_names = {
            key
            for food in food_nutrients
            for key in food.keys()
            if key not in food_field_names
        }
        field_names = food_field_names + sorted(nutrient_field_names)

        with open(food_nutrients_csv, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=field_names, delimiter=';')
            writer.writeheader()
            writer.writerows(food_nutrients)


if __name__ == '__main__':
    fdc = FoodDataCentral()
    foods = list(fdc.food_list())
    print(len(foods))

    csv_generator = CsvGenerator()
    csv_generator.generate_nutrient_definitions_csv()
    csv_generator.generate_food_nutrients_csv()
