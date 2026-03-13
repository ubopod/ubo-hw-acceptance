import logging
import time
import os
import sys

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from PIL import Image, ImageDraw, ImageFont
import qrcode
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
                        self.show_test_screen()
            if self.state_index == 1:
                if (self.test_report["qrcode"] and self.test_report["blue"]
                        and self.test_report["green"] and self.test_report["red"]):
                    lcd.display([(1, "LCD Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Passed", 0, "green"), (4, chr(56), 1, "green")], 30)
                    self.test_result = True
                else:
                    lcd.display([(1, "LCD Test", 0, "white"), (2, "Result:", 0, "white"), (3, "Failed", 0, "red"), (4, chr(50), 1, "red")], 30)
                    self.test_result = False
                time.sleep(2)
                self.state_index = 2

    def show_test_screen(self):
        image = Image.new("RGB", (240, 240), "black")
        draw = ImageDraw.Draw(image)

        # Title and sample text at the top
        try:
            fnt_title = ImageFont.truetype(up_dir + 'rubik/Rubik-Light.ttf', 50)
            fnt_text = ImageFont.truetype(up_dir + 'rubik/Rubik-Light.ttf', 25)
        except Exception:
            fnt_title = ImageFont.load_default()
            fnt_text = ImageFont.load_default()
        draw.text((10, 2), "Title:", fill="white", font=fnt_title)
        draw.text((10, 55), "some text", fill="red", font=fnt_text)

        # QR code in the middle
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=1,
        )
        qr.add_data("ubo-test")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="white", back_color="black").convert("RGB")
        qr_size = min(qr_img.size[0], 90)
        qr_img = qr_img.resize((qr_size, qr_size))
        qr_x = (240 - qr_size) // 2
        image.paste(qr_img, (qr_x, 115))

        # Three colored circles at the bottom
        circle_y = 220
        circle_r = 10
        circle_spacing = 50
        start_x = (240 - (3 * circle_spacing - (circle_spacing - 2 * circle_r))) // 2
        for i, color in enumerate(["red", "green", "blue"]):
            cx = start_x + i * circle_spacing
            draw.ellipse(
                [cx - circle_r, circle_y - circle_r, cx + circle_r, circle_y + circle_r],
                fill=color,
            )

        lcd.show_image(image)
        time.sleep(2)
        if self.repeat_counter == self.num_retries:
            lcd.show_prompt("See QR, text & colors?", [{"text": "Yes", "color": "green"}, {"text": "No", "color": "red"}])
        else:
            lcd.show_prompt("See QR, text & colors?", [{"text": "Yes", "color": "green"}, {"text": "Retry", "color": "red"}])


def main():
    lcd.display([(1, "Starting", 0, "white"), (2, "LCD Display", 0, "white"), (3, "Test", 0, "white")], 25)
    S = state_machine()
    S.show_test_screen()
    logger.debug("Initial state: %d", S.state_index)
    while S.state_index != 2:
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
