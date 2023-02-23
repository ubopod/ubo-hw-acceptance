import time
import os
import sys
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
sys.path.append(up_dir)
from lcd import LCD as LCD
#from ubo_keypad import KEYPAD as KEYPAD
from ubo_keypad import * # Might have to revisit this form of import
from eeprom import *

#initialize LCD and Keypad
lcd = LCD()
lcd.set_lcd_present(1)
#Show Ubo logo
#lcd.show_logo()
# TODO
# Add slide switch test
# After tester presses all buttons
# show slide switch graphics and 
# listen for change in status


class mykeypad(KEYPAD):
    def __init__(self, *args, **kwargs):
        super(mykeypad, self).__init__(*args, **kwargs)
        self.state_index = 0
        self.repeat_counter = 0
        self.test_result  = False
        self.test_report = {"0":False, "1":False, "2":False, "up":False, "down":False, "back":False, "home":False, "mic": True}

    def key_press_cb(self, channel):
        #read inputs
        inputs = self.aw.inputs
        print("Inputs: {:016b}".format(inputs))
        inputs = 127 - inputs & 0x7F
        if inputs < 1:
            return
        index = (int)(math.log2(inputs))
        print("index is " + str(index))
        if inputs > -1:
            print("Key side = " + BUTTONS[index])
            print("state = " + str(self.state_index))
            print("BUTTONS[index]= ", BUTTONS[index])
            if BUTTONS[index]=="0":
                # update test result array
                self.test_report["0"] = True
                # display latest array
            if BUTTONS[index]=="1":
                # update test result array
                self.test_report["1"] = True
                # display latest array
            if BUTTONS[index]=="2":
                # update test result array
                self.test_report["2"] = True
                # display latest array
            if BUTTONS[index]=="up":
                # update test result array
                self.test_report["up"] = True
                # display latest array
            if BUTTONS[index]=="down":
                # update test result array
                self.test_report["down"] = True
                # display latest array
            if BUTTONS[index]=="back":
                # update test result array
                self.test_report["back"] = True
                # display latest array
            if BUTTONS[index]=="home":
                # update test result array
                self.test_report["home"] = True
            lcd.indicate_buttons("Press all", "green", buttons=self.test_report)
            self.test_result = (self.test_report["0"] and self.test_report["1"] and 
                                self.test_report["2"] and self.test_report["up"] and 
                                self.test_report["down"] and self.test_report["home"] and 
                                self.test_report["back"])
            

def main():
    lcd.display([(1,"Starting",0,"white"), (2,"Keypad",0,"white"), (3,"Test", 0,"white")], 25)
    e2p = EEPROM()
    try:
        keypad = mykeypad()
    except:
        # did not detect keypad on i2c bus
        print("failed to initialize keypad")
    if keypad.bus_address ==  False:
        keypad.test_result = False
        #abort test
    else:
        # continue with test
        lcd.indicate_buttons("Press all", "green", keypad.test_result)
        while (not keypad.test_result): # check state machine state 
            time.sleep(1)
    # format test report
    # "keypad": {
    #     "model": "aw9523",
    #     "bus_address": "0x58",
    #     "test_result": true,
    #     "test_report": {
    #             "0": false,
    #             "1": false,
    #             "2": false,
    #             "up": true,
    #             "down": true,
    #             "back": true,
    #             "home": true,
    #             "mic": true
    #         }
    # },
    summary = {"keypad":{}}
    summary["keypad"]["model"] = keypad.model
    summary["keypad"]["bus_address"] = keypad.bus_address
    summary["keypad"]["test_result"] = keypad.test_result
    summary["keypad"]["test_report"] = keypad.test_report
    print(summary)
    e2p.update_json(summary)
    print(keypad.test_result)
    if keypad.test_result:
        lcd.display([(1,"Keypad Test",0,"white"), (2, "Result:", 0, "white"), (3,"Passed",0,"green"), (4,chr(56),1,"green")], 25)
        time.sleep(1)
        sys.exit(0)
    else:
        lcd.display([(1,"Keypad Test",0,"white"), (2, "Result:", 0, "white"), (3,"Failed",0,"red"), (4,chr(50),1,"red")], 25)
        time.sleep(1)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(0)

# lcd.display([(1,"Next:",0,"white"), (2,"big boxes covering all screen:",0,"white"), (2,"red, then green, then blue",0,"white")], 10)
# time.sleep(1)
# for color in ["RED","GREEN","BLUE"]:
#     print(color + " box")
#     image = Image.new("RGB", (240, 240), color)
#     draw = ImageDraw.Draw(image)
#     draw.rectangle((0, 0, 240,240), outline=0, fill=color)
#     lcd.show_image(image)
#     time.sleep(3)
#     #current_result = input("color of box is "+color + "? [y/n]>\t\n")
#     result = result and (current_result == "y")
# #for ch in range(0, 255):
# #   lcd.display([(1,str(ch),0,136),(2,chr(ch),1,"purple")], 40)
# #   time.sleep(1)


