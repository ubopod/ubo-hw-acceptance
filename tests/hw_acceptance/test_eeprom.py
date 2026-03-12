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
from eeprom import HatEEPROM, EEPROMNotFoundError, EEPROMReadError, EEPROMWriteError
from test_report import gen_serial_number, save_serial_number, update_json

MAGIC_ERASE_SERIAL = 'ZNNEK99C84'
ZERO_UUID = '00000000-0000-0000-0000-000000000000'

lcd = LCD()
lcd.set_lcd_present(1)


def program_eeprom(eeprom, serial_number=None, fresh=False):
    """Generate a serial number and write it to EEPROM.

    If fresh=True, writes full settings template (for blank EEPROMs).
    If fresh=False, preserves existing UUID and updates custom data only.
    """
    if serial_number is None:
        serial_number = gen_serial_number()

    summary = {
        "serial_number": serial_number,
        "eeprom": {
            "model": eeprom.model,
            "bus_address": "0x50",
            "test_result": True,
        },
    }

    lcd.display([
        (1, "Generating", 0, "white"),
        (2, "Serial Number:", 0, "white"),
        (3, serial_number, 0, "green"),
        (4, "Updating Data", 0, "white"),
        (5, "Please Wait...", 0, "white"),
    ], 19)

    update_json(summary, filename=serial_number + ".json")

    if fresh:
        eeprom.write(custom_data=[summary])
    else:
        eeprom.update(custom_data=[summary])

    return serial_number


def main():
    lcd.display([
        (1, "Starting", 0, "white"),
        (2, "EEPROM", 0, "white"),
        (3, "Test", 0, "white"),
    ], 20)

    test_result = False
    try:
        with HatEEPROM() as eeprom:
            try:
                content = eeprom.read()
            except EEPROMReadError:
                content = None

            has_valid_uuid = (
                content
                and getattr(content, 'product_uuid', None)
                and content.product_uuid != ZERO_UUID
            )

            if not has_valid_uuid:
                serial_number = program_eeprom(eeprom, fresh=True)

            elif content.custom_data and isinstance(content.custom_data[0], dict):
                custom = content.custom_data[0]
                serial_number = custom.get("serial_number")

                if serial_number == MAGIC_ERASE_SERIAL:
                    lcd.display([
                        (1, "Erasing", 0, "white"),
                        (2, "EEPROM", 0, "white"),
                        (3, "Content", 0, "white"),
                    ], 20)
                    eeprom.reset()
                    lcd.display([
                        (1, "Serial Number:", 0, "white"),
                        (2, serial_number, 0, "green"),
                        (3, "Erased...", 0, "white"),
                    ], 19)
                    serial_number = program_eeprom(eeprom, fresh=True)

                elif serial_number:
                    lcd.display([
                        (1, "Already Has", 0, "white"),
                        (2, "Serial Number:", 0, "white"),
                        (3, serial_number, 0, "green"),
                    ], 19)
                    custom["eeprom"] = {
                        "model": "24c32",
                        "bus_address": "0x50",
                        "test_result": True,
                    }
                    update_json(custom, filename=serial_number + ".json")
                    time.sleep(2)

                else:
                    serial_number = program_eeprom(eeprom)

            elif content.custom_data:
                lcd.display([
                    (1, "Corrupt", 0, "white"),
                    (2, "EEPROM", 0, "white"),
                    (3, "Content!", 0, "white"),
                ], 20)
                time.sleep(1)
                serial_number = program_eeprom(eeprom)

            else:
                serial_number = program_eeprom(eeprom)

            save_serial_number(serial_number)
            test_result = True

    except EEPROMNotFoundError:
        logger.error("No EEPROM IC detected on I2C bus")
        lcd.display([
            (1, "No EEPROM", 0, "white"),
            (2, "IC Detected!", 0, "white"),
            (3, chr(50), 1, "red"),
        ], 20)
        time.sleep(1)

    except (EEPROMReadError, EEPROMWriteError) as e:
        logger.error("EEPROM operation failed: %s", e)

    if test_result:
        logger.info("EEPROM test passed")
        lcd.display([
            (1, "EEPROM", 0, "white"),
            (2, "Test Result:", 0, "white"),
            (3, "Passed", 0, "green"),
            (4, chr(56), 1, "green"),
        ], 22)
        sys.exit(0)
    else:
        logger.info("EEPROM test failed")
        lcd.display([
            (1, "EEPROM", 0, "white"),
            (2, "Test Result:", 0, "white"),
            (3, "Failed", 0, "red"),
            (4, chr(50), 1, "red"),
        ], 22)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
