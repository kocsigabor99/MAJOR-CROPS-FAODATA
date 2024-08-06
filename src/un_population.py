import requests
from functools import cached_property

from common import JSON, get_secret


class UnPopulation:
    """
    Class to interact with the UN Population API

    Documentation

    https://population.un.org/dataportalapi/index.html

    API Key

    In order to use the API, you need to sign up for an API key. You can do so by sending a request
    to population@un.org. The API key is then sent to you via email. Once you have an API key, you
    should store it in a file called `secrets.json` in the `src` directory.
    {
        "UN_POPULATION_API_KEY": "API_KEY_HERE",
    }
    If you do not have an API key, you cannot use the API.
    """

    BASE_URL = 'https://population.un.org/dataportalapi'

    @cached_property
    def headers(self):
        api_key = get_secret('UN_POPULATION_API_KEY')
        return {
            'Authorization': f'Bearer {api_key}'
        }

    def get_indicators(self):
        url = f'{self.BASE_URL}/api/v1/indicators'
        return self._make_get_call(url)

    def get_population_projection(self):
        url = f'{self.BASE_URL}/api/v1/empirical/data'

    def _make_get_call(self, url: str, params: dict = None) -> JSON:
        params = params or {}
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()


if __name__ == '__main__':
    un_population = UnPopulation()
    print(un_population.get_indicators())
    # print(un_population.get_population_projection())
