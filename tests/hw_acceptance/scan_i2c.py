# SPDX-FileCopyrightText: 2017 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""CircuitPython I2C Device Address Scan"""

import logging
import time
import board
import signal
import sys
import os

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from lcd import LCD
from test_report import update_json

lcd = LCD()
lcd.set_lcd_present(1)

i2c = board.I2C()


def _handle_timeout(signum, frame):
    raise TimeoutError("Execution timed out")


signal.signal(signal.SIGALRM, _handle_timeout)


def perform_scan(summary=None):
    if summary is None:
        summary = {"speakers": {}, 'microphones': {}, "temperature": {}, "ambient": {}, "keypad": {}, "i2c_bus": {}, "version": ""}
    while not i2c.try_lock():
        pass

    summary["speakers"]["bus_address"] = False
    summary["microphones"]["bus_address"] = False
    summary["keypad"]["bus_address"] = False
    summary["ambient"]["bus_address"] = False
    summary["temperature"]["bus_address"] = False
    try:
        signal.alarm(5)
        scanned_addressed = [hex(device_address) for device_address in i2c.scan()]
        logger.info("I2C addresses found: %s", scanned_addressed)
        time.sleep(1)
        signal.alarm(0)
    except Exception:
        logger.error("Failed to scan I2C bus")
        summary["i2c_bus"]["status"] = 'slow_bus'
    else:
        logger.info("Successfully scanned I2C bus")
        summary["i2c_bus"]["num_devices"] = len(scanned_addressed)
        summary["i2c_bus"]["scanned_addressed"] = scanned_addressed
        if len(scanned_addressed) > 4:
            logger.warning("More than 4 devices found - I2C bus issue")
            summary["i2c_bus"]["status"] = "bad_bus"
        if len(scanned_addressed) == 0:
            logger.warning("No devices found - I2C bus issue")
            summary["i2c_bus"]["status"] = "open_bus"
        if 0 < len(scanned_addressed) < 4:
            logger.info("Found %d devices on I2C bus", len(scanned_addressed))
            summary["i2c_bus"]["status"] = "functional_bus"
            if '0x1a' in scanned_addressed:
                logger.warning("Audio chip driver is not loaded")
            else:
                if os.system("i2cdetect -y 1 | grep 'UU'") == 0:
                    logger.info("Audio IC detected")
                    summary["speakers"]["bus_address"] = "0x1a"
                    summary["microphones"]["bus_address"] = "0x1a"
                else:
                    logger.warning("No audio IC detected")
            if '0x10' in scanned_addressed:
                logger.info("Light sensor IC detected")
                summary["ambient"]["bus_address"] = '0x10'
            else:
                logger.warning("No light sensor IC detected")
            if '0x48' in scanned_addressed:
                logger.info("Temperature sensor IC detected")
                summary["temperature"]["bus_address"] = '0x48'
            else:
                logger.warning("No temperature sensor IC detected")
            if '0x58' in scanned_addressed:
                logger.info("Keypad GPIO expander IC detected")
                summary["keypad"]["bus_address"] = '0x58'
            else:
                logger.warning("No keypad GPIO expander IC detected")
            # determine SKU
            if (summary["keypad"]["bus_address"] and
                    summary["ambient"]["bus_address"] and
                    summary["temperature"]["bus_address"] and
                    summary["speakers"]["bus_address"]):
                summary["version"] = "V2"
            elif (summary["keypad"]["bus_address"] is not False and
                  summary["ambient"]["bus_address"] is False and
                  summary["temperature"]["bus_address"] is False and
                  summary["speakers"]["bus_address"] is False):
                summary["version"] = "V1"
            else:
                summary["version"] = "unknown"
    finally:
        i2c.unlock()
    return summary


def show_summary(data):
    lines = []
    for key in data:
        module = data[key]
        if type(module) is dict:
            if module.get("bus_address"):
                lines.append((key, chr(56), "white", "green"))
            elif module.get("bus_address") is False:
                lines.append((key, chr(50), "white", "red"))
    lcd.show_summary(lines, size=25)


def main():
    summary = {"speakers": {}, 'microphones': {}, "temperature": {}, "ambient": {}, "keypad": {}, "i2c_bus": {}, "version": ""}
    lcd.display([(1, "Scanning", 0, "white"), (2, "the I2C Bus...", 0, "white")], 20)
    summary = perform_scan(summary)
    show_summary(summary)
    time.sleep(1)
    logger.debug("I2C scan summary: %s", summary)
    update_json(summary)
    if summary["i2c_bus"]["status"] == "slow_bus":
        lcd.display([(1, "No response from", 0, "white"), (2, "I2C Bus!", 0, "white"), (3, chr(50), 1, "red")], 20)
    elif summary["i2c_bus"]["status"] == "open_bus":
        lcd.display([(1, "No devices on", 0, "white"), (2, "I2C Bus!", 0, "white"), (3, chr(50), 1, "red")], 20)
    elif summary["i2c_bus"]["status"] == "bad_bus":
        lcd.display([(1, "Too many devices", 0, "white"), (2, "on I2C Bus!", 0, "white"), (3, chr(50), 1, "red")], 20)
    elif summary["i2c_bus"]["status"] == "functional_bus":
        if summary['keypad']['bus_address'] is False:
            lcd.display([(1, "No Keypad", 0, "white"), (2, "IC detected!", 0, "white"), (3, chr(50), 1, "red")], 20)
        elif summary["version"] == "V1":
            lcd.display([(1, "Minimum SKU", 0, "white"), (2, "Device Found!", 0, "white")], 21)
            time.sleep(2)
            sys.exit(64)
        elif summary["version"] == "V2":
            lcd.display([(1, "Full SKU", 0, "white"), (2, "Device Found!", 0, "white")], 21)
            time.sleep(2)
            sys.exit(65)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
