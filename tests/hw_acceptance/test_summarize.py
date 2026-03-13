import json
import logging
import math
import os
import sys
import time
from datetime import datetime

up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../../'
sys.path.append(up_dir)

from logging_setup import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from lcd import LCD
from ubo_keypad import KEYPAD, BUTTONS
from eeprom import HatEEPROM
from test_report import read_json, update_json, get_serial_number, JSON_PATH
from print_label import print_label
from upload_test_report import upload_file

def load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                os.environ.setdefault(key.strip(), value.strip())

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

lcd = LCD()
bucket_name = "ubo-hw-test-logs"


def show_summary(data):
    lines = []
    for key in data:
        module = data[key]
        if isinstance(module, dict):
            if module.get("test_result") is True:
                lines.append((key, chr(56), "white", "green"))
            elif module.get("test_result") is False:
                lines.append((key, chr(50), "white", "red"))
    lcd.show_summary(lines, size=25)


def power_off():
    lcd.display([
        (1, "Powering Off", 0, "white"),
        (2, "Please Wait..", 0, "white"),
    ], 22)
    time.sleep(1)
    lcd.clear()
    os.system("sudo poweroff")


class SummaryKeypad(KEYPAD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_index = 0
        self.data = {}
        self.label_info = {}

    def key_press_cb(self, channel):
        inputs = self.aw.inputs
        logger.debug("Inputs: {:016b}".format(inputs))
        inputs = 127 - inputs & 0x7F
        if inputs < 1:
            return
        index = int(math.log2(inputs))
        if inputs > -1:
            logger.debug("Key side = %s", BUTTONS[index])
            if self.state_index == 0:
                if BUTTONS[index] == "0":
                    show_summary(self.data)
                    time.sleep(3)
                    lcd.show_menu("Test Finished", ["Summary", "Power Off", "Re-Print"])
                elif BUTTONS[index] == "1":
                    power_off()
                elif BUTTONS[index] == "2":
                    lcd.display([
                        (1, "Printing", 0, "white"),
                        (2, "The Label...", 0, "green"),
                    ], 25)
                    r = print_label(
                        self.label_info['serial_number'],
                        self.label_info['test_result'],
                        self.label_info['test_date'],
                    )
                    if not r:
                        lcd.display([
                            (1, "Printing", 0, "white"),
                            (2, "Failed!", 0, "red"),
                            (3, "Printer is", 0, "white"),
                            (4, "Off!", 0, "red"),
                        ], 24)
                        time.sleep(2)
                    lcd.show_menu("Test Finished", ["Summary", "Power Off", "Re-Print"])


def main():
    serial_number = get_serial_number()
    data, filename = read_json(serial_number=serial_number)
    logger.debug("Test data: %s", data)

    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    summary = {"timedate": date_time}

    all_tests = ('keypad', 'lcd', 'led', 'eeprom', 'speakers',
                  'microphones', 'ambient', 'temperature', 'infrared')
    all_passed = all(data.get(t, {}).get('test_result') for t in all_tests)

    summary["test_result"] = all_passed

    if all_passed:
        lcd.display([
            (1, "All Tests", 0, "white"),
            (2, "Passed!", 0, "green"),
            (3, chr(56), 1, "green"),
        ], 24)
    else:
        lcd.display([
            (1, "Some Tests", 0, "white"),
            (2, "Failed!", 0, "red"),
            (3, chr(50), 1, "red"),
        ], 24)
    time.sleep(2)

    lcd.display([
        (1, "Updating", 0, "white"),
        (2, "EEPROM", 0, "white"),
        (3, "Content...", 0, "white"),
    ], 25)

    update_json(summary, serial_number=serial_number)

    try:
        with HatEEPROM() as eeprom:
            full_data, _ = read_json(serial_number=serial_number)
            eeprom.update(custom_data=[full_data])
    except Exception:
        logger.exception("EEPROM update failed")

    S = SummaryKeypad()
    if serial_number:
        json_filepath = os.path.join(JSON_PATH, serial_number + ".json")
        object_filename = serial_number + ".json"
        SN = serial_number
    else:
        json_filepath = os.path.join(JSON_PATH, "test_summary.json")
        object_filename = "summary_" + now.strftime("%Y%m%d-%H%M%S") + ".json"
        SN = "NO SERIAL#"

    with open(json_filepath) as f:
        S.data = json.load(f)

    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    if not access_key or not secret_key:
        logger.info("AWS credentials not provided — skipping S3 upload")
        upload_result = False
    else:
        upload_result = False
        for attempt in range(4):
            try:
                if attempt == 0:
                    lcd.display([
                        (1, "Uploading File", 0, "white"),
                        (2, object_filename, 0, "green"),
                    ], 15)
                else:
                    lcd.display([
                        (1, "Upload Failed", 0, "white"),
                        (2, "Trying Again...", 0, "white"),
                        (3, "Retry No: " + str(attempt), 0, "red"),
                        (4, json_filepath, 0, "white"),
                    ], 16)
                upload_result = upload_file(json_filepath, bucket_name, object_name=object_filename)
                if upload_result:
                    break
                time.sleep(1)
            except Exception:
                logger.exception("File upload failed (attempt %d)", attempt + 1)

        if upload_result:
            logger.info("File upload succeeded")
            lcd.display([
                (1, "File Upload", 0, "white"),
                (2, "Succeeded", 0, "green"),
                (3, chr(56), 1, "green"),
            ], 25)
        else:
            logger.error("File upload failed after all retries")
            lcd.display([
                (1, "File Upload", 0, "white"),
                (2, "Failed", 0, "red"),
                (3, chr(50), 1, "red"),
            ], 25)

    lcd.display([
        (1, "Printing", 0, "white"),
        (2, "The Label...", 0, "green"),
    ], 25)
    S.label_info = {
        "serial_number": SN,
        "test_result": summary["test_result"],
        "test_date": date_time,
    }
    r = print_label(S.label_info['serial_number'],
                    S.label_info['test_result'],
                    S.label_info['test_date'])
    if not r:
        lcd.display([
            (1, "Printing", 0, "white"),
            (2, "Failed!", 0, "red"),
            (3, "Printer is", 0, "white"),
            (4, "Off!", 0, "red"),
        ], 24)
    time.sleep(1)

    lcd.show_menu("Test Finished", ["Summary", "Power Off", "Re-Print"])
    while S.state_index != 3:
        time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
