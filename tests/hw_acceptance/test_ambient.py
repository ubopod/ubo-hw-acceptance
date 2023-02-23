import time
import board
import adafruit_veml7700
import os
import sys
import neopixel
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
print(up_dir)
sys.path.append(up_dir)
from lcd import LCD as LCD
#from ubo_keypad import KEYPAD as KEYPAD
from ubo_keypad import * # Might have to revisit this form of import
from eeprom import *

lcd = LCD()
lcd.set_lcd_present(1)

i2c = board.I2C()  # uses board.SCL and board.SDA
try:
    veml7700 = adafruit_veml7700.VEML7700(i2c)
    bus_address = "0x10"
except ValueError as e:
    print("VEML7700 not found on I2C bus!")
    bus_address = False
test_result = {}

pixels = neopixel.NeoPixel(board.D12, 27)

def main():
    """ Script to self test ambient light sensor with LED lights"""
    delta = []
    baseline = []
    reading = []
    result = None
    #lcd.display([(1,"Cover the ambient sensor",0,"white"),], 20)
    e2p = EEPROM()
    data, f_json = e2p.read_json()
    if data["led"]["test_result"] == False:
        lcd.display([(1,"Skipping",0,"white"), (2, "Light Sensor", 0, "white"), (3,"Test!",0,"white")], 20)
        result = None
        test_report = {}
        time.sleep(1)
    elif bus_address:
        for i in range(5):
            pixels.fill((0, 0, 0))
            degree = 360*((i+1)/5)
            lcd.progress_wheel("Testing Light Sensor",degree,"white")
            time.sleep(0.3)
            baseline.append(int(veml7700.light))
            print("Baseline ambient light:", baseline)
            time.sleep(0.1)
            pixels.fill((255, 255, 255))
            time.sleep(0.4)
            reading.append(int(veml7700.light))
            time.sleep(0.1)
            print("Stimulated ambient light:", reading)
            delta.append(reading[i] - baseline[i])
            print("Delta = " , delta[i])
        pixels.fill((0, 0, 0))
        average_baseline = sum(baseline) / len(baseline)
        average_reading = sum(reading) / len(reading)
        average_delta = sum(delta) / len(delta)
        if average_delta > 200:
            result = True
        else:
            result = False
        test_report = {
                "works": result,
                "baseline" : average_baseline,
                "reading" : average_reading,
                "delta" : average_delta
            }
    else:
        lcd.display([(1,"No Light Sensor",0,"white"), (2, "IC detected!", 0, "white"), (3,"Failed",0,"red"), (4,chr(50),1,"red")], 20)
        result = False
        test_report = {}
        time.sleep(1)
    # update test report
    # "ambient": {
    # "model": "VEML7700",
    # "bus_address": "0x48",
    # "test_result": true,
    # "test_report": {
    #         "reading" : 15000,
    #         "baseline" : 11000,
    #         "delta" : 4000
    #     }
    # },
    summary = {"ambient":{}}
    summary["ambient"]["model"] = "VEML7700"
    summary["ambient"]["bus_address"] = bus_address
    summary["ambient"]["test_result"] = result
    summary["ambient"]["test_report"] = test_report
    print(summary)
    e2p.update_json(summary)
    print(test_result)
    if result == True:
        # Display Test Result on LCD
        lcd.display([(1,"Light Sensor",0,"white"), (2, "Test Result:", 0, "white"), (3,"Passed",0,"green"), (4,chr(56),1,"green")], 22)
        sys.exit(0)
    elif result == False:
        # Display Test Result on LCD
        lcd.display([(1,"Light Sensor",0,"white"), (2, "Test Result:", 0, "white"), (3,"Failed",0,"red"), (4,chr(50),1,"red")], 22)
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)