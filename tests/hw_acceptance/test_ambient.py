import logging
import time
import board
import adafruit_veml7700
import os
import sys
import neopixel
import statistics

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

NUM_CYCLES = 7
SAMPLES_PER_STATE = 5
STATE_SETTLE_SECONDS = 0.25
SAMPLE_INTERVAL_SECONDS = 0.05
MIN_DELTA_LUX = 200
MIN_GOOD_CYCLES = 5
NOISE_MULTIPLIER = 6


def sample_light(samples=SAMPLES_PER_STATE, delay=SAMPLE_INTERVAL_SECONDS):
    readings = []
    for _ in range(samples):
        readings.append(int(veml7700.light))
        time.sleep(delay)
    return readings


def median_spread(samples):
    return max(samples) - min(samples)


def main():
    delta = []
    baseline = []
    reading = []
    baseline_windows = []
    reading_windows = []
    result = None
    data, f_json = read_json()
    if data["led"]["test_result"] is False:
        lcd.display([(1, "Skipping", 0, "white"), (2, "Light Sensor", 0, "white"), (3, "Test!", 0, "white")], 20)
        result = None
        test_report = {}
        time.sleep(1)
    elif bus_address:
        for i in range(NUM_CYCLES):
            pixels.fill((0, 0, 0))
            degree = 360 * ((i + 1) / NUM_CYCLES)
            lcd.progress_wheel("Testing Light Sensor", degree, "white")
            time.sleep(STATE_SETTLE_SECONDS)
            baseline_window = sample_light()
            baseline_windows.append(baseline_window)
            baseline_median = int(statistics.median(baseline_window))
            baseline.append(baseline_median)
            logger.debug("Baseline ambient light window: %s median=%d", baseline_window, baseline_median)
            pixels.fill((255, 255, 255))
            time.sleep(STATE_SETTLE_SECONDS)
            reading_window = sample_light()
            reading_windows.append(reading_window)
            reading_median = int(statistics.median(reading_window))
            reading.append(reading_median)
            logger.debug("Stimulated ambient light window: %s median=%d", reading_window, reading_median)
            delta_value = reading_median - baseline_median
            delta.append(delta_value)
            logger.debug("Delta = %d", delta_value)
        pixels.fill((0, 0, 0))
        average_baseline = sum(baseline) / len(baseline)
        average_reading = sum(reading) / len(reading)
        average_delta = sum(delta) / len(delta)
        median_baseline = statistics.median(baseline)
        median_reading = statistics.median(reading)
        median_delta = statistics.median(delta)
        baseline_noise = statistics.median([median_spread(window) for window in baseline_windows])
        reading_noise = statistics.median([median_spread(window) for window in reading_windows])
        noise_floor = max(baseline_noise, reading_noise)
        required_delta = max(MIN_DELTA_LUX, noise_floor * NOISE_MULTIPLIER)
        good_cycles = sum(1 for value in delta if value >= required_delta)
        result = median_delta >= required_delta and good_cycles >= MIN_GOOD_CYCLES
        test_report = {
            "works": result,
            "baseline": average_baseline,
            "reading": average_reading,
            "delta": average_delta,
            "baseline_median": median_baseline,
            "reading_median": median_reading,
            "delta_median": median_delta,
            "required_delta": required_delta,
            "good_cycles": good_cycles,
            "num_cycles": NUM_CYCLES,
            "baseline_noise": baseline_noise,
            "reading_noise": reading_noise,
            "cycle_deltas": delta,
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
