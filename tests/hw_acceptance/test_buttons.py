import logging
import time
import os
import sys

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


class mykeypad(KEYPAD):
    def __init__(self, *args, **kwargs):
        super(mykeypad, self).__init__(*args, **kwargs)
        self.state_index = 0
        self.repeat_counter = 0
        self.test_result = False
        self.test_report = {"0": False, "1": False, "2": False, "up": False, "down": False, "back": False, "home": False, "mic": True}

    def key_press_cb(self, channel):
        inputs = self.aw.inputs
        logger.debug("Inputs: {:016b}".format(inputs))
        inputs = 127 - inputs & 0x7F
        if inputs < 1:
            return
        index = int(math.log2(inputs))
        logger.debug("index=%d key=%s state=%d", index, BUTTONS[index], self.state_index)
        if inputs > -1:
            if BUTTONS[index] in self.test_report:
                self.test_report[BUTTONS[index]] = True
            lcd.indicate_buttons("Press all", "green", buttons=self.test_report)
            self.test_result = (self.test_report["0"] and self.test_report["1"] and
                                self.test_report["2"] and self.test_report["up"] and
                                self.test_report["down"] and self.test_report["home"] and
                                self.test_report["back"])


def main():
    lcd.display([(1, "Starting", 0, "white"), (2, "Keypad", 0, "white"), (3, "Test", 0, "white")], 25)
    try:
        keypad = mykeypad()
    except Exception:
        logger.error("Failed to initialize keypad")
        return
    if keypad.bus_address is False:
        keypad.test_result = False
    else:
        lcd.indicate_buttons("Press all", "green", keypad.test_result)
        while not keypad.test_result:
            time.sleep(1)
    summary = {"keypad": {}}
    summary["keypad"]["model"] = keypad.model
    summary["keypad"]["bus_address"] = keypad.bus_address
    summary["keypad"]["test_result"] = keypad.test_result
    summary["keypad"]["test_report"] = keypad.test_report
    logger.debug("Keypad summary: %s", summary)
    update_json(summary)
    logger.info("Keypad test result: %s", keypad.test_result)
    if keypad.test_result:
        lcd.display([(1, "Keypad Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 25)
        time.sleep(1)
        sys.exit(0)
    else:
        lcd.display([(1, "Keypad Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 25)
        time.sleep(1)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(1)
