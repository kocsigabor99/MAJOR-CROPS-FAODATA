import json
import os.path

SRC_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(ROOT_DIR)
JSON = None | bool | int | float | str | list['JSON'] | dict[str, 'JSON']


def get_secret(secret_key: str) -> JSON:
    with open(os.path.join(SRC_DIR, 'secrets.json')) as f:
        secrets = json.load(f)
    return secrets[secret_key]
