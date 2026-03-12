import logging
import time
import os
import sys
import board
import adafruit_pct2075

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


def main():
    try:
        result = None
        pct = adafruit_pct2075.PCT2075(i2c, address=0x48)
        bus_address = "0x48"
        temperature = pct.temperature
        logger.info("Temperature is %.2f C", temperature)
        lcd.display([(1, "Room:", 0, "white"), (2, "Temperature:", 0, "white"), (3, str(temperature), 0, "green")], 22)
        time.sleep(1)
        if 0 < temperature < 50:
            result = True
        else:
            result = False
    except Exception:
        logger.error("Failed to detect temperature sensor on I2C bus")
        lcd.display([(1, "No Temperature", 0, "white"), (2, "Sensor IC", 0, "white"), (3, "Detected!", 0, "white"), (4, "Failed", 0, "red"), (4, chr(56), 1, "red")], 18)
        time.sleep(1.5)
        temperature = False
        bus_address = False
        result = False
    summary = {"temperature": {}}
    summary["temperature"]["model"] = "pct2075"
    summary["temperature"]["bus_address"] = bus_address
    summary["temperature"]["test_result"] = result
    summary["temperature"]["test_report"] = {"degrees": temperature}
    logger.debug("Temperature summary: %s", summary)
    update_json(summary)
    if result:
        lcd.display([(1, "Temperature", 0, "white"), (2, "Sensor Test:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 21)
        sys.exit(0)
    else:
        lcd.display([(1, "Temperature", 0, "white"), (2, "Sensor", 0, "white"), (3, "Test:", 0, "white"), (4, "Failed", 0, "red"), (4, chr(56), 1, "red")], 21)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
