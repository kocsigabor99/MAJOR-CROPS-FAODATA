import base64
import csv
import hashlib
import json
import os.path
import random
from functools import cached_property
from operator import itemgetter
from typing import Generator, Literal, TypedDict

import requests

from common import DATA_DIR, JSON, get_secret

random.seed(684)

FdcDataType = Literal['Branded', 'Foundation', 'Survey (FNDDS)', 'SR Legacy']


class NutrientDict(TypedDict):
    """
    Example of a nutrient dictionary:
    {
        "number": "268",
        "name": "Energy",
        "unitName": "kJ",
        "derivationCode": "NC",
        "derivationDescription": "Calculated"
    }
    """

    number: str
    name: str
    unitName: str
    derivationCode: str
    derivationDescription: str


class FoodNutrientDict(NutrientDict):
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

    amount: float


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
    dataType: FdcDataType
    publicationDate: str
    ndbNumber: str
    foodNutrients: list[FoodNutrientDict]


class FoodDataCentral:
    """
    Class to interact with the USDA Food Data Central API

    Documentation

    More info on: https://fdc.nal.usda.gov/api-guide.html
    API docs on: https://app.swaggerhub.com/apis/fdcnal/food-data_central_api/1.0.1#/

    API key

    In order to use the API, you need to get an API key from: https://fdc.nal.usda.gov/api-key-signup.html
    You can get an API key for free. With it, you can make 3600 requests per hour.
    Once you have an API key, you should store it in a file called `secrets.json` in the `src` directory.
    {
        "FOOD_DATA_CENTRAL_API_KEY": "API_KEY_HERE",
    }
    If you do not have an API key, you can still use this class with a demo key. This demo key is limited to
    30 requests per IP address per hour and 50 requests per IP address per day. In order to fetch all data in
    as little requests as possible, it is recommended to increase the page size to 200 (which is the API's maximum).
    The default page size of 50 is used in this class to have more readable cached json files.

    Cache

    The API responses are cached in the `data/fdc_cache` directory. This is to avoid making the same request
    multiple times. The cache is stored as JSON files with the URL as the filename. The URL is hashed using
    SHA-256 and then encoded using base64. The cache is only used for GET requests. If you want to force a
    request to the API, you can delete the corresponding cache file.
    """

    BASE_URL = 'https://api.nal.usda.gov/fdc'

    @cached_property
    def api_key(self) -> str:
        """
        Get the API key from the secrets file, or return a demo key if no proper API key has been defined
        """

        try:
            return get_secret('FOOD_DATA_CENTRAL_API_KEY')
        except (KeyError, FileNotFoundError, json.JSONDecodeError):
            return 'DEMO_KEY'

    def food_list(self, data_types: list[FdcDataType] = None) -> Generator[FoodDict, None, None]:
        """
        Get an iterator over all food items in the database of the given data type

        :param data_types: Data types you are interested in.
                           If None, food items from Foundation and SR Legacy are returned.
        :return: Generator over all food items with their nutrients in the FDC database
        """

        if not data_types:
            data_types = ['Foundation', 'SR Legacy']

        url = 'v1/foods/list'
        params = {
            'dataType': ','.join(data_types),
        }
        yield from self._make_paginated_get_call(url, params)

    def get_food(self, fdc_id: int, nutrients: list[str] = None) -> FoodDict:
        """
        Get a specific food item by its FDC ID

        :param fdc_id: FDC identifier of the food item
        :param nutrients: Nutrients you are interested in. If None, all nutrients are returned
        :return: Food item with its nutrients for the given FDC ID
        """

        url = f'v1/food/{fdc_id}'
        nutrients = ','.join(nutrients) if nutrients else None
        return self._make_get_call(url, params={'nutrients': nutrients})  # noqa

    def _make_paginated_get_call(self, url: str, params: dict = None) -> Generator[JSON, None, None]:
        """
        Make a paginated GET call to the API

        :param url: URL to make the GET call to
        :param params: Parameters to pass in the GET call. This could include a `pageSize`,
                       but if not provided, it will default to 50
        :return: Generator over all items in the paginated response
        """

        params = params or {}
        if 'pageSize' not in params:
            params['pageSize'] = 50
        page = 1
        while True:
            params['pageNumber'] = page
            data = self._make_get_call(url, params)
            if not data:
                break
            # Verify that the returned data is indeed a list to yield from
            if not isinstance(data, list):
                raise ValueError(f'Expected a list, but got {type(data)}')
            yield from data
            page += 1

    def _make_get_call(self, url: str, params: dict = None) -> JSON:
        """
        Make a GET call to the API

        :param url: URL to make the GET call to
        :param params: Parameters to pass in the GET call
        """

        # We build the URL with the parameters instead of using params in requests.get(),
        # in order to have a consistent URL for the cache
        url = f'{self.BASE_URL}/{url}'
        params = params or {}
        url_params = '&'.join([f'{key}={value}' for key, value in params.items()])
        if url_params:
            url = f'{url}?{url_params}'

        # Check if the response is already in the cache
        data = self._get_response_from_cache(url)

        # If the response is not in the cache yet, get the response from the API and add it to the cache
        if data is None:
            response = requests.get(url, params={'api_key': self.api_key})
            response.raise_for_status()
            data = response.json()
            self._add_response_to_cache(url, data)

            ratelimit_remaining = response.headers.get('X-Ratelimit-Remaining')
            ratelimit_limit = response.headers.get('X-Ratelimit-Limit')
            print(f'Added response from {url} to cache. Remaining calls: {ratelimit_remaining}/{ratelimit_limit}')

        return data

    @staticmethod
    def _hash_url_to_alphanumeric(url: str) -> str:
        """
        Hash a URL to an alphanumeric string

        >>> FoodDataCentral._hash_url_to_alphanumeric('https://example.com')
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

        url_hash = self._hash_url_to_alphanumeric(url)
        cache_file = os.path.join(DATA_DIR, 'fdc_cache', f'{url_hash}.json')
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                return json.load(f)
        return None

    def _add_response_to_cache(self, url: str, data: JSON):
        """
        Add a response to the cache
        """

        url_hash = self._hash_url_to_alphanumeric(url)
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
        """
        Get a list of all food items in the FDC database through the FDC API
        Cache the result in the class, so we don't need to fetch the data multiple times
        """

        return list(self.fdc.food_list())

    def generate_nutrient_definitions_csv(self) -> str:
        """
        Generate a CSV file with the definitions of all nutrients

        :return: Path to the generated CSV file

        Snippet from file:
        number;name;unitName;derivationCode;derivationDescription
        ;Verbascose;G;A;Analytical
        202;Nitrogen;G;A;Analytical
        203;Protein;G;;
        """

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
        nutrients = sorted(result.values(), key=itemgetter('number'))

        nutrients_csv = os.path.join(self.FDC_DATA_DIR, 'nutrient_definitions.csv')
        with open(nutrients_csv, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=nutrients[0].keys(), delimiter=';')
            writer.writeheader()
            writer.writerows(nutrients)

        print(f'Successfully written {len(nutrients)} nutrient definitions to {nutrients_csv}')
        return nutrients_csv

    def generate_food_nutrients_csv(self) -> str:
        """
        Generate a CSV file with all food nutrients

        :return: Path to the generated CSV file

        Snippet from file:
        fdcId;description;dataType;publicationDate;ndbNumber;;202;203;204;205
        167512;Pillsbury Golden Layer Biscuits, refrigerated dough;SR Legacy;2019-04-01;18634;;;5.88;13.2;41.2
        167513;Pillsbury, Cinnamon Rolls with Icing, refrigerated dough;SR Legacy;2019-04-01;18635;;;4.34;11.3;53.4
        167514;Kraft Foods, Shake N Bake Original Recipe, Coating for Pork;SR Legacy;2019-04-01;18637;;;6.1;3.7;79.8
        167515;George Weston Bakeries, Thomas English Muffins;SR Legacy;2019-04-01;18639;;;8.0;1.8;46.0
        """

        # Flatten the food nutrients into a list of dictionaries
        food_nutrients = [
            {
                'fdcId': food['fdcId'],
                'description': food['description'],
                'dataType': food['dataType'],
                'publicationDate': food['publicationDate'],
                'ndbNumber': food['ndbNumber'],
                **{nutrient['number']: nutrient.get('amount', 0) for nutrient in food['foodNutrients']}
            }
            for food in self.food_list
        ]
        food_nutrients.sort(key=itemgetter('fdcId'))

        # Write the food nutrients to a CSV file
        food_nutrients_csv = os.path.join(self.FDC_DATA_DIR, 'food_nutrients.csv')

        # Concatenate all keys from all dictionaries into a set
        all_field_names = {key for food in food_nutrients for key in food.keys()}
        food_field_names = ['fdcId', 'description', 'dataType', 'publicationDate', 'ndbNumber']
        nutrient_field_names = sorted(all_field_names - set(food_field_names))
        field_names = food_field_names + nutrient_field_names

        # Write the CSV file
        with open(food_nutrients_csv, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=field_names, delimiter=';')
            writer.writeheader()
            writer.writerows(food_nutrients)

        print(f'Successfully written {len(food_nutrients)} food nutrients to {food_nutrients_csv}')
        return food_nutrients_csv


class Explorer:
    """
    Class to manually explore the large csv files generated by CsvGenerator
    """

    NUTRIENT_DEFINITIONS_CSV = os.path.join(DATA_DIR, 'fdc_data', 'nutrient_definitions.csv')
    FOOD_NUTRIENTS_CSV = os.path.join(DATA_DIR, 'fdc_data', 'food_nutrients.csv')

    @cached_property
    def nutrients(self) -> dict[str, NutrientDict]:
        """
        Return the nutrients for a given food item
        """

        with open(self.NUTRIENT_DEFINITIONS_CSV) as f:
            reader = csv.DictReader(f, delimiter=';')
            return {row['number']: row for row in reader}  # noqa

    @cached_property
    def food_nutrients(self) -> dict[str, dict[str, str]]:
        """
        Return the food nutrients for a given food item
        """

        with open(self.FOOD_NUTRIENTS_CSV) as f:
            reader = csv.DictReader(f, delimiter=';')
            return {row['fdcId']: row for row in reader}  # noqa

    def print_snippet(self, path_to_file: str):
        """
        Print the first 5 lines and first 10 columns of the given CSV file

        :param path_to_file: Path to the CSV file to print
        """

        with open(path_to_file) as f:
            reader = csv.reader(f, delimiter=';')
            for i, row in enumerate(reader):
                if i >= 5:
                    break
                print(';'.join(row[:10]))

    def write_food_item_names(self) -> str:
        """
        Write a list of names of food items

        :return: Path to the generated JSON file
        """

        names_json = os.path.join(DATA_DIR, 'fdc_data', 'exploration', 'food_item_names.json')
        names = sorted([row['description'] for row in self.food_nutrients.values()])
        with open(names_json, 'w') as f:
            json.dump(names, f, indent=2)
        return names_json

    def top_n_per_nutrient(self, top_n: int) -> str:
        """
        Write per nutrient the number and name, and the top N foods with the highest amount of that nutrient

        :param top_n: Path to the generated JSON file
        """

        top_n_per_nutrient_json = os.path.join(DATA_DIR, 'fdc_data', 'exploration', f'top_{top_n}_per_nutrient.json')
        top_n_per_nutrient = {}
        for nutrient_number, nutrient in self.nutrients.items():
            nutrient_name = nutrient['name']
            nutrient_unit_name = nutrient['unitName']
            top_n_per_nutrient[nutrient_number] = {
                'number': nutrient_number,
                'name': nutrient_name,
                'unitName': nutrient_unit_name,
                'top_n_foods': sorted(
                    [
                        {
                            'fdcId': food['fdcId'],
                            'description': food['description'],
                            'amount': float(food[nutrient_number] or '0'),
                        }
                        for food in self.food_nutrients.values()
                        if nutrient_number in food
                    ],
                    key=lambda x: x['amount'],
                    reverse=True,
                )[:top_n],
            }
        with open(top_n_per_nutrient_json, 'w') as f:
            json.dump(top_n_per_nutrient, f, indent=2)
        return top_n_per_nutrient_json

    def print_food_item(self, fdcid: int, energy_only: bool = False):
        """
        Print the food item with the given FDC ID and the specified nutrients
        """

        food = self.food_nutrients[str(fdcid)]
        print(f'Food item: {food["description"]}')
        for nutrient_number, nutrient in self.nutrients.items():
            amount = food.get(nutrient_number, '')  # noqa
            if amount and float(amount) > 0 and (not energy_only or 'Energy' in nutrient['name']):
                print(f'{nutrient["name"]}: {amount} {nutrient["unitName"]}')

    def make_csv_shorter(self):
        """
        Make the CSV file shorter by:
        - Use only the selected columns
        - Take 100 random rows
        """

        nutrients_to_keep = [
            'Protein',
            'Energy',
            'Fiber, total dietary',
            'Calcium, Ca',
            'Magnesium, Mg',
            'Vitamin B-6',
            'Vitamin B-12',
            'Vitamin C, total ascorbic acid',
        ]
        with open(self.NUTRIENT_DEFINITIONS_CSV) as f:
            reader = csv.DictReader(f, delimiter=';')
            nutrients = [row['number'] for row in reader if row['name'] in nutrients_to_keep]
            if '208' in nutrients and '268' in nutrients:
                # Energy in kCal (208) and Energy in KJ (268) are representing the same, so we only need one
                nutrients.remove('268')

        with open(self.FOOD_NUTRIENTS_CSV) as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = [row for row in reader]

            # Take 100 random rows
            random_rows = random.sample(rows, 100)

            # Remove the columns that are not in the selected nutrients
            print(random_rows[0])
            headers =  ['fdcId', 'description'] + nutrients
            shorter_rows = [{key: value for key, value in row.items() if key in headers} for row in random_rows]

            # Replace the numeric keys with the nutrient names
            for row in shorter_rows:
                for nutrient_number in nutrients:
                    row[self.nutrients[nutrient_number]['name']] = row.pop(nutrient_number)
            headers = ['fdcId', 'description'] + [self.nutrients[nutrient_number]['name'] for nutrient_number in nutrients]

            # Write the shorter CSV file
            shorter_csv = os.path.join(DATA_DIR, 'fdc_data', 'food_nutrients_short.csv')
            with open(shorter_csv, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=headers, delimiter=';')
                writer.writeheader()
                writer.writerows(shorter_rows)


if __name__ == '__main__':
    # fdc = FoodDataCentral()
    # foods = list(fdc.food_list())
    # print(len(foods))

    # csv_generator = CsvGenerator()
    # csv_generator.generate_nutrient_definitions_csv()
    # csv_generator.generate_food_nutrients_csv()

    explorer = Explorer()
    # explorer.print_snippet(explorer.FOOD_NUTRIENTS_CSV)
    # explorer.write_food_item_names()
    # explorer.top_n_per_nutrient(10)
    # for fcdid in [168271, 171029, 171400]:
    #     explorer.print_food_item(fcdid, energy_only=True)
    #     print()
    explorer.make_csv_shorter()
