import RPi.GPIO as GPIO
from adafruit_bus_device import i2c_device
import adafruit_aw9523
from PIL import Image, ImageDraw, ImageFont
import logging
import board
import math
import time
import signal
import os
import sys
up_dir = os.path.dirname(os.path.abspath(__file__)) + '/../'
sys.path.append(up_dir)
try:
    from self.configparser import configparser
except ImportError:
    import configparser
display = True

logger = logging.getLogger(__name__)

DIR = './ui/'
CONFIG_FILE = './config/config.ini'
STATUS_FILE = './info/status.ini'
INT_EXPANDER = 5
BUTTONS = ["0", "1", "2", "up", "down", "back", "home", "mic"]


class KEYPAD(object):

    def __init__(self):
        # self.config = configparser.ConfigParser()
        # self.config.read(CONFIG_FILE)
        # self.status = configparser.ConfigParser()
        # self.status.read(STATUS_FILE)
        # self.logger = logging.getLogger("keypad")
        self.display_active = False
        self.window_stack = []
        self.led_enabled = True
        # self.led_client = LEDClient()
        #if (int(self.config.get('hw', 'button-version'))) == 1:
        #    # this is an old model, no need for the keypad service
        #    print("old keypad")
        #    self.enabled = False
        #    return
        #else:
        logger.info("Initializing keypad")
        self.aw = None
        self.mic_switch_status = False
        self.last_inputs = None
        self.bus_address = False
        self.model = "aw9523"
        self.init_i2c()
        self.enabled = True

        
    def init_i2c(self):
        GPIO.setmode(GPIO.BCM)
        i2c = board.I2C()
        # Set this to the GPIO of the interrupt:
        GPIO.setup(INT_EXPANDER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        try:
            self.aw = adafruit_aw9523.AW9523(i2c, 0x58)
            new_i2c = i2c_device.I2CDevice(i2c, 0x58)
            self.bus_address = "0x58"
        except Exception:
            try:
                self.aw = adafruit_aw9523.AW9523(i2c, 0x5b)
                new_i2c = i2c_device.I2CDevice(i2c, 0x5b)
                self.bus_address = "0x5b"
            except Exception:
                self.bus_address = False
                logger.error("Failed to initialize I2C Bus")
                return
        self.aw.reset()
        self.aw.directions = 0xff00
        time.sleep(1)
        # first write to both registers to reset the interrupt flag
        buffer = bytearray(2)
        buffer[0] = 0x00
        buffer[1] = 0x00
        new_i2c.write(buffer)
        new_i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)
        logger.debug("Register 0x00: %s", buffer)
        time.sleep(0.1)
        buffer[0] = 0x01
        buffer[1] = 0x00
        new_i2c.write(buffer)
        new_i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)
        logger.debug("Register 0x01: %s", buffer)
        # disable interrupt for higher bits
        buffer[0] = 0x06
        buffer[1] = 0x00
        new_i2c.write(buffer)
        new_i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)
        logger.debug("Register 0x06: %s", buffer)
        buffer[0] = 0x07
        buffer[1] = 0xff
        new_i2c.write(buffer)
        new_i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)
        logger.debug("Register 0x07: %s", buffer)
        # read registers again to reset interrupt
        buffer[0] = 0x00
        buffer[1] = 0x00
        new_i2c.write(buffer)
        new_i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)
        logger.debug("Register 0x00 (reset): %s", buffer)
        time.sleep(0.1)
        buffer[0] = 0x01
        buffer[1] = 0x00
        new_i2c.write(buffer)
        new_i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)
        logger.debug("Register 0x01 (reset): %s", buffer)
        time.sleep(0.1)
        self.last_inputs = self.aw.inputs
        logger.debug("Inputs: {:016b}".format(self.last_inputs))
        logger.debug("Mic bit: 0x%02x", self.last_inputs & 0x80)
        self.mic_switch_status = ((self.last_inputs & 0x80) == 128)
        logger.info("Mic switch is %s", self.mic_switch_status)
        time.sleep(0.5)
        time.sleep(0.5)
        GPIO.add_event_detect(INT_EXPANDER, GPIO.FALLING, callback=self.key_press_cb)
        #GPIO.add_event_detect(INT_EXPANDER, GPIO.BOTH, callback=self.key_press_cb, bouncetime=200)

    def key_press_cb(self, channel):
        self.last_inputs = self.aw.inputs
        logger.debug("Inputs: {:016b}".format(self.last_inputs))
        inputs = 127 - self.last_inputs & 0x7F
        if inputs == 0:
            logger.debug("No keypad change")
            if ((self.last_inputs & 0x80) == 0) and \
                (self.mic_switch_status is True):
                logger.info("Mic Switch is now OFF")
                self.mic_switch_status = False
            if ((self.last_inputs & 0x80) == 128) and \
                (self.mic_switch_status is False):
                logger.info("Mic Switch is now ON")
                self.mic_switch_status = True
            return
        index = int(math.log2(inputs))
        logger.debug("index=%d key=%s", index, BUTTONS[index])
        if inputs > -1:
            logger.debug("Key %s on %d", BUTTONS[index], index)
            return BUTTONS[index]

    def get_mic_switch_status(self):
        inputs = self.aw.inputs
        logger.debug("Inputs: {:016b}".format(inputs))
        return ((inputs & 0x80) == 128)




def main():
    keypad = KEYPAD()
    if keypad.enabled is False:
        return
    s = "OFF"
    if keypad.led_enabled:
        s = "ON"
    while True:
        time.sleep(100)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
