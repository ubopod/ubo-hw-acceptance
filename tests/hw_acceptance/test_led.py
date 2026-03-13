import board
import logging
import os
import sys
import neopixel
import time

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from lcd import LCD
from ubo_keypad import KEYPAD, BUTTONS, math
from test_report import update_json

lcd = LCD()
lcd.set_lcd_present(1)

pixels = neopixel.NeoPixel(board.D12, 27)


def wheel(pos):
    """Generate rainbow color for position 0-255."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)


class mykeypad(KEYPAD):
    def __init__(self, *args, **kwargs):
        super(mykeypad, self).__init__(*args, **kwargs)
        self.state_index = 0
        self.repeat_counter = 0
        self.test_report = {"green": False, "red": False, "blue": False}
        self.test_result = False
        self.num_retries = 1

    def key_press_cb(self, channel):
        inputs = self.aw.inputs
        logger.debug("Inputs: {:016b}".format(inputs))
        inputs = 127 - inputs & 0x7F
        if inputs < 1:
            return
        index = int(math.log2(inputs))
        logger.debug("index=%d key=%s state=%d", index, BUTTONS[index], self.state_index)
        if inputs > -1:
            if self.state_index == 0:
                if BUTTONS[index] == "1":
                    self.test_report["red"] = True
                    self.test_report["green"] = True
                    self.test_report["blue"] = True
                    self.state_index = 1
                    self.repeat_counter = 0
                if BUTTONS[index] == "2":
                    self.repeat_counter += 1
                    if self.repeat_counter > self.num_retries:
                        self.state_index = 1
                        self.repeat_counter = 0
                    else:
                        self.show_rainbow()
            if self.state_index == 1:
                if self.test_report["blue"] and self.test_report["green"] and self.test_report["red"]:
                    lcd.display([(1, "LED Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 30)
                    self.test_result = True
                else:
                    lcd.display([(1, "LED Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 30)
                    self.test_result = False
                time.sleep(2)
                self.state_index = 2

    def show_rainbow(self):
        for i in range(27):
            pixels[i] = wheel(int(i * 255 / 27))
        pixels.show()
        if self.repeat_counter == self.num_retries:
            lcd.show_prompt("Do you see a rainbow ring?", [{"text": "Yes", "color": "green"}, {"text": "No", "color": "red"}])
        else:
            lcd.show_prompt("Do you see a rainbow ring?", [{"text": "Yes", "color": "green"}, {"text": "Retry", "color": "red"}])


def main():
    lcd.display([(1, "Starting", 0, "white"), (2, "LED Ring", 0, "white"), (3, "Test", 0, "white")], 25)
    state_machine = mykeypad()
    time.sleep(0.5)
    state_machine.show_rainbow()
    logger.debug("Initial state: %d", state_machine.state_index)
    while state_machine.state_index != 2:
        time.sleep(1)
    pixels.fill((0, 0, 0))
    summary = {"led": {}}
    summary["led"]["model"] = "neopixel"
    summary["led"]["count"] = 27
    summary["led"]["test_result"] = state_machine.test_result
    summary["led"]["test_report"] = state_machine.test_report
    logger.debug("LED summary: %s", summary)
    update_json(summary)
    logger.info("LED test result: %s", state_machine.test_result)
    if state_machine.test_result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
