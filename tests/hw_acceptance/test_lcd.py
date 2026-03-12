import logging
import time
import os
import sys

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from PIL import Image, ImageDraw
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
        self.test_result = False
        self.test_report = {"qrcode": False, "green": False, "red": False, "blue": False}
        if lcd.version == 3:
            self.lcd_model = "st7789"
            self.lcd_resolution = "240x240"
        elif lcd.version == 2:
            self.lcd_model = "ssd1306"
            self.lcd_resolution = "128x64"

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
                    self.test_report["qrcode"] = True
                    self.state_index = 1
                    self.repeat_counter = 0
                    self.show_color_and_prompt("red")
                if BUTTONS[index] == "2":
                    self.repeat_counter += 1
                    if self.repeat_counter > self.num_retries:
                        self.test_report["qrcode"] = False
                        self.state_index = 1
                        self.repeat_counter = 0
                        self.show_color_and_prompt("red")
                    else:
                        self.show_color_and_prompt("qrcode")
            elif self.state_index == 1:
                if BUTTONS[index] == "1":
                    self.test_report["red"] = True
                    self.state_index = 2
                    self.repeat_counter = 0
                    self.show_color_and_prompt("green")
                if BUTTONS[index] == "2":
                    self.repeat_counter += 1
                    if self.repeat_counter > self.num_retries:
                        self.test_report["red"] = False
                        self.state_index = 2
                        self.repeat_counter = 0
                        self.show_color_and_prompt("green")
                    else:
                        self.show_color_and_prompt("red")
            elif self.state_index == 2:
                logger.debug("state = %d", self.state_index)
                if BUTTONS[index] == "1":
                    self.test_report["green"] = True
                    self.state_index = 3
                    self.repeat_counter = 0
                    self.show_color_and_prompt("blue")
                if BUTTONS[index] == "2":
                    self.repeat_counter += 1
                    if self.repeat_counter > self.num_retries:
                        self.test_report["green"] = False
                        self.state_index = 3
                        self.repeat_counter = 0
                        self.show_color_and_prompt("blue")
                    else:
                        self.show_color_and_prompt("green")
            elif self.state_index == 3:
                if BUTTONS[index] == "1":
                    self.test_report["blue"] = True
                    self.state_index = 4
                    self.repeat_counter = 0
                if BUTTONS[index] == "2":
                    self.repeat_counter += 1
                    if self.repeat_counter > self.num_retries:
                        self.test_report["blue"] = False
                        self.repeat_counter = 0
                        self.state_index = 4
                    else:
                        self.show_color_and_prompt("blue")
            if self.state_index == 4:
                if (self.test_report["qrcode"] and self.test_report["blue"]
                        and self.test_report["green"] and self.test_report["red"]):
                    lcd.display([(1, "LCD Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 30)
                    self.test_result = True
                else:
                    lcd.display([(1, "LCD Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 30)
                    self.test_result = False
                time.sleep(2)
                self.state_index = 5

    def show_color_and_prompt(self, content):
        if content == "qrcode":
            lcd.display([(1, "Title:", 0, "white"), (2, "some text", 0, "red"), (3, "zxcvbnmmm,./asdfghjkl;qwertyuiop", 2, "green")], 20)
            time.sleep(2)
            if self.repeat_counter == self.num_retries:
                lcd.show_prompt("Did you see text & QR code?", [{"text": "Yes", "color": "green"}, {"text": "No", "color": "red"}])
            else:
                lcd.show_prompt("Did you see text & QR code?", [{"text": "Yes", "color": "green"}, {"text": "Retry", "color": "red"}])
        if content in ["green", "red", "blue"]:
            color = content
            image = Image.new("RGB", (240, 240), color)
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 240, 240), outline=0, fill=color)
            lcd.show_image(image)
            time.sleep(0.5)
            message = "Did you see a " + color + " screen?"
            if self.repeat_counter == self.num_retries:
                lcd.show_prompt(message, [{"text": "Yes", "color": "green"}, {"text": "No", "color": "red"}])
            else:
                lcd.show_prompt(message, [{"text": "Yes", "color": "green"}, {"text": "Retry", "color": "red"}])


def main():
    lcd.display([(1, "Starting", 0, "white"), (2, "LCD Display", 0, "white"), (3, "Test", 0, "white")], 25)
    S = state_machine()
    S.show_color_and_prompt("qrcode")
    logger.debug("Initial state: %d", S.state_index)
    while S.state_index != 5:
        time.sleep(1)
    logger.info("LCD test result: %s", S.test_result)
    summary = {"lcd": {}}
    summary["lcd"]["model"] = S.lcd_model
    summary["lcd"]["resolution"] = S.lcd_resolution
    summary["lcd"]["test_result"] = S.test_result
    summary["lcd"]["test_report"] = S.test_report
    update_json(summary)
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
