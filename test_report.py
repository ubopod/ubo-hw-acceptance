import json
import logging
import os
import random

logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(PROJECT_DIR, 'tests', 'hw_acceptance', 'test_results')
_SERIAL_CACHE = os.path.join(JSON_PATH, '.serial_number')

os.makedirs(JSON_PATH, exist_ok=True)

_SERIAL_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"


def gen_serial_number(length=12):
    return ''.join(random.SystemRandom().choice(_SERIAL_CHARS) for _ in range(length))


def save_serial_number(serial_number):
    with open(_SERIAL_CACHE, 'w') as f:
        f.write(serial_number)


def get_serial_number():
    try:
        with open(_SERIAL_CACHE) as f:
            sn = f.read().strip()
            return sn if sn else None
    except FileNotFoundError:
        return None


def read_json(serial_number=None, filename=None):
    if filename is None:
        serial_number = serial_number or get_serial_number()
        filename = (serial_number + ".json") if serial_number else "test_summary.json"
    filepath = os.path.join(JSON_PATH, filename)
    try:
        with open(filepath) as f:
            return json.load(f), filename
    except FileNotFoundError:
        logger.warning("File not found: %s. Using empty summary.", filepath)
        return {}, filename


def update_json(summary, serial_number=None, filename=None):
    if filename is None:
        serial_number = serial_number or get_serial_number()
        filename = (serial_number + ".json") if serial_number else "test_summary.json"
    data, filename = read_json(filename=filename)
    data.update(summary)
    filepath = os.path.join(JSON_PATH, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    return data, filename
