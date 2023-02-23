# SPDX-FileCopyrightText: 2017 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""CircuitPython I2C Device Address Scan"""
# If you run this and it seems to hang, try manually unlocking
# your I2C bus from the REPL with
#  >>> import board
#  >>> board.I2C().unlock()

import time
import board
import signal
import sys
import os
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
sys.path.append(up_dir)
from lcd import LCD as LCD
from eeprom import *

lcd = LCD()
lcd.set_lcd_present(1)

# To use default I2C bus (most boards)
i2c = board.I2C()
# print(dir(board))

# To create I2C bus on specific pins
# import busio
#i2c = busio.I2C(board.SCL0, board.SDA0)  # QT Py RP2040 STEMMA connector
# i2c = busio.I2C(board.GP1, board.GP0)    # Pi Pico RP2040

def _handle_timeout(signum,frame):
    raise TimeoutError("Execution timed out")

signal.signal(signal.SIGALRM, _handle_timeout)   


def perform_scan(summary = None):
    if summary is None:
        summary = {"speakers":{}, 'microphones':{}, "temperature":{}, "ambient":{}, "keypad":{}, "i2c_bus":{}, "version":""}
    while not i2c.try_lock():
        pass

    #set default values
    summary["speakers"]["bus_address"] = False
    summary["microphones"]["bus_address"] = False
    summary["keypad"]["bus_address"] = False
    summary["ambient"]["bus_address"] = False
    summary["temperature"]["bus_address"] = False
    try:
        signal.alarm(5)
        scanned_addressed = [hex(device_address) for device_address in i2c.scan()]
        print(
            "I2C addresses found:",
            scanned_addressed,
        )
        time.sleep(1)
        signal.alarm(0) 
    except:
        #raise
        # it took too long to scan the I2C bus
        print("Failed to scan I2C bus")
        summary["i2c_bus"]["status"] = 'slow_bus'
        # display error message on LCD
        # skip a bunch of tests
    else:
        print("Successfull scanned I2C bus")
        summary["i2c_bus"]["num_devices"] = len(scanned_addressed)
        summary["i2c_bus"]["scanned_addressed"] = scanned_addressed
        if len(scanned_addressed) > 4:
            print("More than 4 devices found")
            print("There's an issue with I2C bus")
            summary["i2c_bus"]["status"] = "bad_bus"
        if len(scanned_addressed) == 0:
            print("No devices found")
            print("There's an issue with I2C bus")
            summary["i2c_bus"]["status"] = "open_bus"
        if 0 < len(scanned_addressed) < 4:
            print("Less than 4 devices found")
            summary["i2c_bus"]["status"] = "functional_bus"
            # check if audio chip id detected and driver is loaded
            if '0x1a' in scanned_addressed:
                print("Audio chip driver is not loaded!")
            else:
                #scan for UU address
                if (os.system("i2cdetect -y 1 | grep 'UU'") == 0):
                    print("audio IC detected!")
                    summary["speakers"]["bus_address"] = "0x1a"
                    summary["microphones"]["bus_address"] = "0x1a"
                else:
                    print("No audio IC detected!")
            # check if light sensor is connected
            if '0x10' in scanned_addressed:
                print("Light sensor IC is detected!")
                summary["ambient"]["bus_address"] = '0x10'
            else:
                print("No light sensor IC detected!")
            #check if temperature sensor IC is detected
            if '0x48' in scanned_addressed:
                print("Temperature sensor IC is detected!")
                summary["temperature"]["bus_address"] = '0x48'
            else:
                print("No temperature sensor IC detected!")
            # check if keypad IC is detected
            if '0x58' in scanned_addressed:
                print("Keypad GPIO expander IC is detected!")
                summary["keypad"]["bus_address"] = '0x58'
            # elif '0x5b' in scanned_addressed:
            #     print("Keypad GPIO expander IC is detected!")
            #     summary["keypad"]["bus_address"] = '0x5b'
            else:
                print("No keypad GPIO expander IC detected!")
            # determine SKU
            if summary["keypad"]["bus_address"] and \
                    summary["ambient"]["bus_address"] and \
                    summary["temperature"]["bus_address"] and \
                    summary["speakers"]["bus_address"]:
                summary["version"] = "V2"
            elif summary["keypad"]["bus_address"] != False and \
                (summary["ambient"]["bus_address"] == False and \
                 summary["temperature"]["bus_address"] == False and \
                 summary["speakers"]["bus_address"] == False ):
                summary["version"] = "V1"
            else:
                summary["version"] = "unknown"
        # I2C addresses found: 16 => '0x10' | 72 => '0x48' | 88 => '0x58'
        # > Audio chip: 0x1a (it is unavailable if driver is loaded, UU)
        # > Temperature sensor chip: 0x48, or 72 decimal
        # > Light sensor chip: 0x10 or 16 decimal
        # > Keypad (GPIO expander) chip: 0x58 or 88 decimal
        # look deeper into what addresses were found
    finally:
        i2c.unlock()
    return summary

def show_summary(data):
    lines = []
    for key in data:
        module = data[key]
        if type(module) is dict:
            if module.get("bus_address"):
                lines.append((key, chr(56), "white", "green"))
            elif module.get("bus_address") == False:
                lines.append((key, chr(50), "white", "red"))
    lcd.show_summary(lines, size=25)

def power_off():
    lcd.display([(1,"Powering Off",0,"white"), (2,"Please Wait..",0,"white")], 22)
    time.sleep(10)
    lcd.clear()
    os.system("sudo poweroff")

def main():
    e2p = EEPROM()
    summary = {"speakers":{}, 'microphones':{}, "temperature":{}, "ambient":{}, "keypad":{}, "i2c_bus":{}, "version":""}
    lcd.display([(1,"Scanning",0,"white"), (2,"the I2C Bus...",0,"white")], 20)
    summary = perform_scan(summary)
    show_summary(summary)
    time.sleep(1)
    print(summary)
    e2p.update_json(summary)
    if summary["i2c_bus"]["status"] == "slow_bus":
        lcd.display([(1,"No response from",0,"white"), (2, "I2C Bus!", 0, "white"), (3,chr(50),1,"red")], 20)
        #time.sleep(20)
        #power_off()
    elif summary["i2c_bus"]["status"] == "open_bus":
        lcd.display([(1,"No devices on",0,"white"), (2, "I2C Bus!", 0, "white"), (3,chr(50),1,"red")], 20)
        #time.sleep(20)
        #power_off()
    elif summary["i2c_bus"]["status"] == "bad_bus":
        lcd.display([(1,"Too many devices",0,"white"), (2, "on I2C Bus!", 0, "white"), (3,chr(50),1,"red")], 20)
        #time.sleep(20)
        #power_off()
    elif summary["i2c_bus"]["status"] == "functional_bus":
        if summary['keypad']['bus_address'] is False:
            lcd.display([(1,"No Keypad",0,"white"), (2, "IC detected!", 0, "white"), (3,chr(50),1,"red")], 20)
            #time.sleep(20)
            #power_off()
        elif summary["version"] == "V1":
            lcd.display([(1,"Minimum SKU",0,"white"), (2,"Device Found!",0,"white")], 21)
            time.sleep(2)
            # exit with code 64 to indicate that the device is a V1 device  
            sys.exit(64)
        elif summary["version"] == "V2":
            lcd.display([(1,"Full SKU",0,"white"), (2,"Device Found!",0,"white")], 21)
            time.sleep(2)
            # exit with code 65 to indicate that the device is a V2 device
            sys.exit(65)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
