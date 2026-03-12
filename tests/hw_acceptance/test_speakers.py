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


class state_machine(KEYPAD):
    def __init__(self, *args, **kwargs):
        super(state_machine, self).__init__(*args, **kwargs)
        self.state_index = 0
        self.repeat_counter = 0
        self.num_retries = 1
        self.test_report = {"left": False, "right": False}
        self.test_result = False
        self.check_i2c()

    def check_i2c(self):
        if os.system("i2cdetect -y 1 | grep 'UU'") == 0:
            logger.info("Audio IC detected")
            self.bus_address = "0xa1"
        else:
            logger.warning("No audio IC detected")
            self.bus_address = False
            self.test_result = False

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
                    self.test_report["left"] = True
                    self.play_sound_and_prompt("right")
                    self.state_index = 1
                if BUTTONS[index] == "2":
                    self.repeat_counter += 1
                    if self.repeat_counter > self.num_retries:
                        self.test_report["left"] = False
                        self.state_index = 1
                        self.repeat_counter = 0
                        self.play_sound_and_prompt("right")
                    else:
                        self.play_sound_and_prompt("left")
            elif self.state_index == 1:
                if BUTTONS[index] == "1":
                    self.test_report["right"] = True
                    self.state_index = 2
                if BUTTONS[index] == "2":
                    self.repeat_counter += 1
                    if self.repeat_counter > self.num_retries:
                        self.test_report["right"] = False
                        self.state_index = 2
                        self.repeat_counter = 0
                    else:
                        self.play_sound_and_prompt("right")
            if self.state_index == 2:
                if self.test_report["left"] and self.test_report["right"]:
                    lcd.display([(1, "Speaker", 0, "white"), (2, "Test:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 25)
                    self.test_result = True
                else:
                    lcd.display([(1, "Speaker", 0, "white"), (2, "Test:", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 25)
                    self.test_result = False
                time.sleep(2)
                self.state_index = 3

    def play_sound_and_prompt(self, channel):
        lcd.display([(1, "Playing", 0, "white"), (2, "audio on", 0, "white"), (3, "the " + channel, 0, "green"), (4, "channel", 0, "white")], 25)
        os.system("aplay -D plughw:CARD=seeed2micvoicec,DEV=0 -c 2 -f S16_LE " + channel + ".wav")
        message = "Did you hear " + channel + " channel?"
        if self.repeat_counter == self.num_retries:
            lcd.show_prompt(message, [{"text": "Yes", "color": "green"}, {"text": "No", "color": "red"}])
        else:
            lcd.show_prompt(message, [{"text": "Yes", "color": "green"}, {"text": "Retry", "color": "red"}])


def main():
    S = state_machine()
    logger.debug("Initial state: %d", S.state_index)
    if S.bus_address:
        S.play_sound_and_prompt("left")
        while S.state_index != 3:
            time.sleep(1)
    else:
        lcd.display([(1, "No Audio", 0, "white"), (2, "IC detected!", 0, "white"), (3, chr(50), 1, "red")], 20)
        time.sleep(1)
    summary = {"speakers": {}}
    summary["speakers"]["model"] = "wm8960"
    summary["speakers"]["bus_address"] = "0x1a"
    summary["speakers"]["test_result"] = S.test_result
    summary["speakers"]["test_report"] = S.test_report
    logger.debug("Speaker summary: %s", summary)
    update_json(summary)
    logger.info("Speaker test result: %s", S.test_result)
    if S.test_result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
