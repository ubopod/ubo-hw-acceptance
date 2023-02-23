import time
import board
import os
import sys
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
print(up_dir)
sys.path.append(up_dir)
from lcd import LCD as LCD
#from ubo_keypad import KEYPAD as KEYPAD
from ubo_keypad import * # Might have to revisit this form of import
from eeprom import *

#initialize LCD
lcd = LCD()
lcd.set_lcd_present(1)



class state_machine(KEYPAD):
    def __init__(self, *args, **kwargs):
        super(state_machine, self).__init__(*args, **kwargs)
        self.state_index = 0
        self.repeat_counter = 0
        self.num_retries = 1
        self.test_report  = {"left":False, "right":False}
        self.test_result = False
        self.check_i2c()

    def check_i2c(self):
        if (os.system("i2cdetect -y 1 | grep 'UU'") == 0):
            print("audio IC detected!")
            self.bus_address = "0xa1"
        else:
            print("No audio IC detected!")
            self.bus_address = False
            self.test_result = False

    def key_press_cb(self, channel):
        #read inputs
        self.last_inputs = self.aw.inputs
        print("Inputs: {:016b}".format(self.last_inputs))
        inputs = 127 - self.last_inputs & 0x7F
        if inputs == 0:
            print("no keypad change")
            print(self.last_inputs & 0x80)
            if ((self.last_inputs & 0x80) == 0) and \
                (self.mic_switch_status == True):
                print("Mic Switch is now OFF")
                self.mic_switch_status = False
            if ((self.last_inputs & 0x80) == 128) and \
                (self.mic_switch_status == False):
                print("Mic Switch is now ON")
                self.mic_switch_status = True
            return
        index = (int)(math.log2(inputs))
        print("index is " + str(index))
        if inputs > -1:
            print("Key side = " + BUTTONS[index])
            print("state = " + str(self.state_index))
            print("BUTTONS[index]= ", BUTTONS[index])
            if self.state_index == 0:
                if BUTTONS[index]=="1": #YES
                    self.test_report["left"] = True # record test result
                    self.play_sound_and_prompt("mic_test_right.wav") # show next screen
                    self.state_index = 1 # move to next state
                if BUTTONS[index]=="2": #RETRY
                    # increment counter
                    self.repeat_counter += 1
                    if (self.repeat_counter > self.num_retries):
                       self.test_report["left"] = False
                       # move to next test/state
                       self.state_index = 1
                       self.repeat_counter = 0
                       self.play_sound_and_prompt("mic_test_right.wav")
                    else:
                        self.play_sound_and_prompt("mic_test_left.wav")
            elif self.state_index == 1:
                if BUTTONS[index]=="1": #YES
                    self.test_report["right"] = True # record test result
                    self.state_index = 2 # move to next state
                if BUTTONS[index]=="2": #RETRY
                    # increment counter
                    self.repeat_counter += 1
                    if (self.repeat_counter > self.num_retries):
                       self.test_report["right"] = False
                       # move to next test/state
                       self.state_index = 2
                       self.repeat_counter = 0
                    else:
                        self.play_sound_and_prompt("mic_test_right.wav")
            if self.state_index == 2:
                #show test result
                if (self.test_report["left"] and self.test_report["right"]):
                    # Display Test Result on LCD
                    lcd.display([(1,"Microphone",0,"white"), (2, "Test:", 0, "white"), (3,"Passed",0,"green"), (4,chr(56),1,"green")], 25)
                    self.test_result = True
                else:
                    lcd.display([(1,"Microphone",0,"white"), (2, "Test:", 0, "white"), (3,"Failed",0,"red"), (4,chr(50),1,"red")], 25)
                    self.test_result = False
                time.sleep(2)
                self.state_index = 3
    def play_sound_and_prompt(self, filename):
        if "left" in filename:
            lcd.display([(1,"Playing back",0,"white"), (2,"Left Mic ",0,"white"),  (3, "..." , 0, "white")], 23)
        else:
            lcd.display([(1,"Playing back",0,"white"), (2,"Right Mic",0,"white"),  (3, "..." , 0, "white")], 23)
        #os.system("amixer set Master 70%")
        os.system("aplay -D plughw:CARD=seeed2micvoicec,DEV=0 -c 1 -f S16_LE " + filename )
        message = "Did you hear your voice?"
        if self.repeat_counter == self.num_retries:
            lcd.show_prompt(message, [{"text": "Yes", "color": "green"},{"text": "No", "color": "red"}] )
        else:
            lcd.show_prompt(message, [{"text": "Yes", "color": "green"},{"text": "Retry", "color": "red"}] )            


def main():
    S = state_machine()
    e2p = EEPROM()
    data, f_json = e2p.read_json()
    # get microphone switch status and if it's off 
    # ask the operator to slide the switch
    if data["speakers"]["test_report"]["left"] == False and data["speakers"]["test_report"]["right"] == False:
        lcd.display([(1,"Skipping",0,"white"), (2, "Microphones", 0, "white"), (3,"Test!",0,"white")], 20)
        time.sleep(1)
        summary = {"microphones":{}}
        summary["microphones"]["model"] = "wm8960"
        summary["microphones"]["bus_address"] = S.bus_address
        summary["microphones"]["test_result"] = None
        summary["microphones"]["test_report"] = {}
    elif S.bus_address:
        if not S.mic_switch_status:
            print("mic switch is off...")
            lcd.display([(1,"Slide Mic",0,"white"), (2, "Switch to", 0, "white"), (3,"the Right",0,"white")], 20)
        while (S.mic_switch_status == False):
            time.sleep(0.5)
        # staty in this state 
        # Display message on LCD
        lcd.display([(1,"Say Something",0,"white"), (2, "for 5 seconds", 0, "white"), (3,"to test mic",0,"white")], 20)
        # notify user that Ubo is going to record audio
        #os.seteuid(1000)
        #os.system("amixer set Master 70%") 
        os.system("aplay -D plughw:CARD=seeed2micvoicec,DEV=0 -c 1 -f S16_LE mic_test_instructions.wav" )
        #os.system("amixer set Master 20%")
        os.system("aplay -D plughw:CARD=seeed2micvoicec,DEV=0 -c 1 -f S16_LE beep.wav" )
        lcd.display([(1,"Recording",0,"white"), (2, "your voice", 0, "white"), (3,"...",0,"white")], 23)
        # Display message on LCD
        # record audio for 5 seconds
        os.system("arecord -D plughw:CARD=seeed2micvoicec,DEV=0 --duration=5 --file-type=wav \
                --format=S16_LE  --rate=16000 --channels=2 mic_test.wav \
                ")
        # split files
        os.system("ffmpeg -y -i mic_test.wav -map_channel 0.0.0 \
        mic_test_left.wav -map_channel 0.0.1 mic_test_right.wav \
        ")
        S.play_sound_and_prompt("mic_test_left.wav")
        print(S.state_index)
        while (S.state_index != 3): # check state machine state 
            time.sleep(1)
    # update json file
    # "microphones": {
    #     "model": "wm8960",
    #     "bus_address": "0x1a",
    #     "test_result": true,
    #     "test_report": {
    #                 "right": false,
    #                 "left": false
    #     }
    # },
        summary = {"microphones":{}}
        summary["microphones"]["model"] = "wm8960"
        summary["microphones"]["bus_address"] = S.bus_address
        summary["microphones"]["test_result"] = S.test_result
        summary["microphones"]["test_report"] = S.test_report
    else:
        lcd.display([(1,"No Audio",0,"white"), (2, "IC detected!", 0, "white"), (3,chr(50),1,"red")], 20)
        time.sleep(1)
        summary = {"microphones":{}}
        summary["microphones"]["model"] = "wm8960"
        summary["microphones"]["bus_address"] = False
        summary["microphones"]["test_result"] = False
        summary["microphones"]["test_report"] = {}
    print(summary)
    e2p.update_json(summary)
    print(S.test_result)
    if S.test_result:
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

