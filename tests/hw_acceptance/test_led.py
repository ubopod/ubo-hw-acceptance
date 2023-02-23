import board
import os
import sys
import neopixel
import time
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
sys.path.append(up_dir)
from lcd import LCD as LCD
#from ubo_keypad import KEYPAD as KEYPAD
from ubo_keypad import * # Might have to revisit this form of import
from eeprom import *

result = True
#initialize LCD and Keypad
lcd = LCD()
lcd.set_lcd_present(1)

pixels = neopixel.NeoPixel(board.D12, 27)



class mykeypad(KEYPAD):
    def __init__(self, *args, **kwargs):
        super(mykeypad, self).__init__(*args, **kwargs)
        self.state_index = 0
        self.repeat_counter = 0
        self.test_report  = {"green":False, "red":False, "blue":False }
        self.test_result = False
        self.num_retries = 0

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
            if self.state_index == 0:
                if BUTTONS[index]=="1": #YES
                    self.test_report["red"] = True # record test result
                    self.show_color_and_prompt("green") # show next screen
                    self.state_index = 1 # move to next state
                if BUTTONS[index]=="2": #RETRY
                    # show QR code for 5 seconds then promot
                    # increment counter
                    self.repeat_counter += 1
                    if (self.repeat_counter > self.num_retries):
                       self.test_report["red"] = False
                       # move to next test/state
                       self.state_index = 1
                       self.repeat_counter = 0
                       self.show_color_and_prompt("green")
                    else:
                        self.show_color_and_prompt("red")
            elif self.state_index == 1:
                print("state = " + str(self.state_index))
                if BUTTONS[index]=="1": #YES
                    self.test_report["green"] = True # record test result
                    self.show_color_and_prompt("blue") # show next screen
                    self.state_index = 2 # move to next state
                if BUTTONS[index]=="2": #RETRY
                    # repeat showing green screen
                    # increment counter
                    self.repeat_counter += 1
                    if (self.repeat_counter > self.num_retries):
                       self.test_report["green"] = False
                       # move to next test/state
                       self.state_index = 2
                       self.repeat_counter = 0
                       self.show_color_and_prompt("blue")
                    else:
                        self.show_color_and_prompt("green")
            elif self.state_index == 2:
                if BUTTONS[index]=="1": #YES
                    self.test_report["blue"] = True # record test result
                    # go to final state
                    self.state_index = 3 # move to next state
                if BUTTONS[index]=="2": #RETRY
                    # show QR code for 5 seconds then promot
                    # increment counter
                    self.repeat_counter += 1
                    if (self.repeat_counter > self.num_retries):
                       self.test_report["blue"] = False
                       # move to next test/state
                       self.repeat_counter = 0
                       self.state_index = 3
                    else:
                       self.show_color_and_prompt("blue")
            if self.state_index == 3:
                #show test result
                if (self.test_report["blue"] and self.test_report["green"] and self.test_report["red"]):
                    # Display Test Result on LCD
                    lcd.display([(1,"LED Test",0,"white"), (2, "Result:", 0, "white"), (3,"Passed",0,"green"), (4,chr(56),1,"green")], 30)
                    self.test_result = True
                else:
                    lcd.display([(1,"LED Test",0,"white"), (2, "Result:", 0, "white"), (3,"Failed",0,"red"), (4,chr(50),1,"red")], 30)
                    self.test_result = False
                time.sleep(2)
                self.state_index = 4
    def show_color_and_prompt(self, color):
        pixels.fill((0, 0, 0))
        if color in ["green", "red", "blue"]:
            # for i in range(27):
            #     #test red
            #     degree = 360*((i+1)/27)
            #     # print(degree)
            #     lcd.progress_wheel("Scanning LEDs...",degree,color)
            #     pixels[i] = ((255/2)*(color=="red"), 
            #                 (255/2)*(color=="green"), 
            #                 (255/2)*(color=="blue"))
            #     #time.sleep(0.05)
            pixels.fill(((255/2)*(color=="red"), 
                        (255/2)*(color=="green"), 
                        (255/2)*(color=="blue")))
            # time.sleep(0.5)
            message = "Is " + color + " led ring complete?"
            if self.repeat_counter == self.num_retries:
                lcd.show_prompt(message, [{"text": "Yes", "color": "green"},{"text": "No", "color": "red"}] )
            else:
                lcd.show_prompt(message, [{"text": "Yes", "color": "green"},{"text": "Retry", "color": "red"}] )


def main():
    lcd.display([(1,"Starting",0,"white"), (2,"LED Ring",0,"white"), (3,"Test", 0,"white")], 25)
    state_machine = mykeypad()
    time.sleep(0.5)
    state_machine.show_color_and_prompt("red")
    e2p = EEPROM()
    print(state_machine.state_index)
    while (state_machine.state_index != 4): # check state machine state 
        time.sleep(1)
    pixels.fill((0, 0, 0))
    # write test result to EEPROM
    # "led": {
    # "model": "neopixel",
    # "count": "27",
    # "test_result": true,
    # "test_report": {
    #         "red": false,
    #         "green": false,
    #         "blue": true
    #     }
    # },
    summary = {"led":{}}
    summary["led"]["model"] = "neopixel"
    summary["led"]["count"] = 27
    summary["led"]["test_result"] = state_machine.test_result
    summary["led"]["test_report"] = state_machine.test_report
    print(summary)
    e2p.update_json(summary)
    print(state_machine.test_result)
    if state_machine.test_result:
        sys.exit(0)
    else:
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

