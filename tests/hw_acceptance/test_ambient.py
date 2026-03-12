import logging
import time
import board
import adafruit_veml7700
import os
import sys
import neopixel

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from lcd import LCD
from test_report import read_json, update_json

lcd = LCD()
lcd.set_lcd_present(1)

i2c = board.I2C()
try:
    veml7700 = adafruit_veml7700.VEML7700(i2c)
    bus_address = "0x10"
except ValueError:
    logger.warning("VEML7700 not found on I2C bus")
    bus_address = False

pixels = neopixel.NeoPixel(board.D12, 27)


def main():
    delta = []
    baseline = []
    reading = []
    result = None
    data, f_json = read_json()
    if data["led"]["test_result"] is False:
        lcd.display([(1, "Skipping", 0, "white"), (2, "Light Sensor", 0, "white"), (3, "Test!", 0, "white")], 20)
        result = None
        test_report = {}
        time.sleep(1)
    elif bus_address:
        for i in range(5):
            pixels.fill((0, 0, 0))
            degree = 360 * ((i + 1) / 5)
            lcd.progress_wheel("Testing Light Sensor", degree, "white")
            time.sleep(0.3)
            baseline.append(int(veml7700.light))
            logger.debug("Baseline ambient light: %s", baseline)
            time.sleep(0.1)
            pixels.fill((255, 255, 255))
            time.sleep(0.4)
            reading.append(int(veml7700.light))
            logger.debug("Stimulated ambient light: %s", reading)
            delta.append(reading[i] - baseline[i])
            logger.debug("Delta = %d", delta[i])
        pixels.fill((0, 0, 0))
        average_baseline = sum(baseline) / len(baseline)
        average_reading = sum(reading) / len(reading)
        average_delta = sum(delta) / len(delta)
        result = average_delta > 200
        test_report = {
            "works": result,
            "baseline": average_baseline,
            "reading": average_reading,
            "delta": average_delta,
        }
    else:
        lcd.display([(1, "No Light Sensor", 0, "white"), (2, "IC detected!", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 20)
        result = False
        test_report = {}
        time.sleep(1)
    summary = {"ambient": {}}
    summary["ambient"]["model"] = "VEML7700"
    summary["ambient"]["bus_address"] = bus_address
    summary["ambient"]["test_result"] = result
    summary["ambient"]["test_report"] = test_report
    logger.debug("Ambient summary: %s", summary)
    update_json(summary)
    if result is True:
        logger.info("Light sensor test passed")
        lcd.display([(1, "Light Sensor", 0, "white"), (2, "Test Result:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 22)
        sys.exit(0)
    elif result is False:
        logger.info("Light sensor test failed")
        lcd.display([(1, "Light Sensor", 0, "white"), (2, "Test Result:", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 22)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
