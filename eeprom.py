import os

from rpi_eeprom import EEPROM, EEPROMConfig
from rpi_eeprom import (
    EEPROMNotFoundError,
    EEPROMReadError,
    EEPROMWriteError,
    EEPROMConfigError,
)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
EEPROM_SETTINGS = os.path.join(
    PROJECT_DIR, 'tests', 'hw_acceptance', 'eeprom_files', 'eeprom_settings.txt',
)

DEFAULT_CONFIG = EEPROMConfig(
    model="24c32",
    size_kbytes=4,
    write_protect_pin=16,
    settings_template=EEPROM_SETTINGS,
)


class HatEEPROM:
    """Thin wrapper around rpi_eeprom.EEPROM with project-specific defaults."""

    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG
        self.model = self.config.model
        self._eeprom = None

    def __enter__(self):
        self._eeprom = EEPROM(self.config)
        self._eeprom.__enter__()
        return self

    def __exit__(self, *args):
        if self._eeprom:
            self._eeprom.__exit__(*args)

    def read(self):
        return self._eeprom.read()

    def write(self, custom_data):
        self._eeprom.write(custom_data=custom_data)

    def update(self, custom_data, **kwargs):
        self._eeprom.update(custom_data=custom_data, **kwargs)

    def reset(self):
        self._eeprom.reset()

    def read_device_tree(self, index=0):
        return self._eeprom.read_device_tree(index=index)
