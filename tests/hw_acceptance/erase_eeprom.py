import logging
import os
import sys
import time

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from lcd import LCD
from eeprom import HatEEPROM, EEPROMNotFoundError

lcd = LCD()
lcd.set_lcd_present(1)


def main():
    lcd.display([
        (1, "Erasing", 0, "white"),
        (2, "EEPROM", 0, "white"),
        (3, "Content", 0, "white"),
    ], 20)
    try:
        with HatEEPROM() as eeprom:
            eeprom.reset()
            lcd.display([
                (1, "EEPROM Reset", 0, "white"),
                (2, "Successful!", 0, "white"),
                (3, chr(56), 1, "green"),
            ], 20)
    except EEPROMNotFoundError:
        logger.error("No EEPROM IC detected on I2C bus")
        lcd.display([
            (1, "No EEPROM", 0, "white"),
            (2, "IC Detected!", 0, "white"),
            (3, chr(50), 1, "red"),
        ], 20)
        time.sleep(1)
    except Exception:
        logger.exception("EEPROM reset failed")
        lcd.display([
            (1, "EEPROM Reset", 0, "white"),
            (2, "Failed!", 0, "white"),
            (3, chr(50), 1, "red"),
        ], 20)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
