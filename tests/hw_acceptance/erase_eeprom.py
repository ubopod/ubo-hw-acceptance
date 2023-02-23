# This script resets the EEPROM to blank state

import time
import board
import os
import sys
import string
import random
import json

up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
print(up_dir)
sys.path.append(up_dir)
from lcd import LCD as LCD
from eeprom import *
lcd = LCD()
lcd.set_lcd_present(1)


def main():
    """ Script to self test EEPROM"""
    test_result = False
    info = {}
    lcd.display([(1,"Erasing",0,"white"), (2,"EEPROM",0,"white"), (3,"Content", 0,"white")], 20)
    e2p = EEPROM()
    if not e2p.bus_address:
        # check if eeprom ic2bus is working
        lcd.display([(1,"No EEPROM",0,"white"), (2,"IC Detected!",0,"white"), (3,chr(50),1,"red")], 20)
        time.sleep(1)
        # abort procedure here...
        return
    try:
        e2p.reset_eeprom()
        lcd.display([(1,"EEPROM Reset",0,"white"), (2,"Successful!",0,"white"), (3,chr(56),1,"green")], 20)
    except Exception as e:
        print(e)
        lcd.display([(1,"EEPROM Reset",0,"white"), (2,"Failed!",0,"white"), (3,chr(50),1,"red")], 20)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
