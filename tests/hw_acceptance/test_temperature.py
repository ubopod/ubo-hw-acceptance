import time
import os
import sys
import board
import adafruit_pct2075
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
sys.path.append(up_dir)
from lcd import LCD as LCD
from eeprom import *

lcd = LCD()
lcd.set_lcd_present(1)
i2c = board.I2C()

def main():
    e2p = EEPROM()
    try:
        result = None
        pct = adafruit_pct2075.PCT2075(i2c, address=0x48)
        bus_address = "0x48"
        temperature = pct.temperature
        print("Temperature is %.2f C" % temperature)
        lcd.display([(1,"Room:",0,"white"), (2,"Temperature:",0,"white"), (3,str(temperature),0,"green"),], 22)
        time.sleep(1)
        if (temperature > 0) and (temperature < 50):
            result = True
        else:
            # double check result with operator
            result = False
    except:
        # failed to detect sensor on I2C bus
        # log incident
        lcd.display([(1,"No Temperature",0,"white"), (2, "Sensor IC", 0, "white"), (3, "Detected!", 0, "white") ,(4,"Failed",0,"red"), (4,chr(56),1,"red")], 18)
        time.sleep(1.5)
        temperature = False
        bus_address = False
        result = False
        pass
    # update test report json file
    # "temperature": {
    # "model": "pct2075",
    # "bus_address": "0x10",
    # "test_result": true,
    # "test_report": {
    #         "degrees" : 32.5
    #     }
    # },
    summary = {"temperature":{}}
    summary["temperature"]["model"] = "pct2075"
    summary["temperature"]["bus_address"] = bus_address
    summary["temperature"]["test_result"] = result
    summary["temperature"]["test_report"] = {"degrees" : temperature}
    print(summary)
    e2p.update_json(summary)
    if result:
        lcd.display([(1,"Temperature",0,"white"), (2, "Sensor Test:", 0, "white") ,(3,"Passed",0,"green"), (4,chr(56),1,"green")], 21)
        sys.exit(0)
    else:
        lcd.display([(1,"Temperature",0,"white"), (2, "Sensor", 0, "white"), (3, "Test:", 0, "white") ,(4,"Failed",0,"red"), (4,chr(56),1,"red")], 21)
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