import board
import os
import sys
import neopixel
import time
from datetime import datetime
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
sys.path.append(up_dir)
from lcd import LCD as LCD
from ubo_keypad import * # Might have to revisit this form of import
from eeprom import *
from print_label import print_label
from upload_test_report import upload_file
os.system("export AWS_SHARED_CREDENTIALS_FILE=/home/pi/.aws/credentials")

# initialize LCD
lcd = LCD()
# S3 bucket name
bucket_name = "ubo-hw-test-logs"


def show_summary(data):
    lines = []
    for key in data:
        module = data[key]
        if type(module) is dict:
            if module.get("test_result") == True:
                lines.append((key, chr(56), "white", "green"))
            elif module.get("test_result") == False:
                lines.append((key, chr(50), "white", "red"))
    lcd.show_summary(lines, size=25)

def power_off():
    lcd.display([(1,"Powering Off",0,"white"), (2,"Please Wait..",0,"white")], 22)
    time.sleep(1)
    lcd.clear()
    os.system("sudo poweroff")

def reboot():
    lcd.display([(1,"Rebooting",0,"white"), (2,"Please Wait..",0,"white")], 22)
    os.system("sudo reboot")

class state_machine(KEYPAD):
    def __init__(self, *args, **kwargs):
        super(state_machine, self).__init__(*args, **kwargs)
        self.state_index = 0
        self.repeat_counter = 0
        self.test_result = False
        self.num_retries = 1
        self.data = {}
        self.label_info = {}

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
                if BUTTONS[index]=="0": #YES
                    # show symmary
                    self.state_index = 1
                    show_summary(self.data)
                    time.sleep(3)
                    lcd.show_menu("Test Finished", ["Summary", "Power Off", "Re-Print"])
                    self.state_index = 0
                    print("button 0 was pressed")
                if BUTTONS[index]=="1": #YES
                    # power off
                    print("button 1 was pressed")
                    power_off()
                if BUTTONS[index]=="2":
                    print("button 2 was pressed")
                    # re-printing label
                    lcd.display([(1,"Printing",0,"white"), (2,"The Label...",0,"green")], 25)
                    r = print_label(self.label_info['serial_number'], 
                                    self.label_info['test_result'],
                                    self.label_info['test_date'])
                    if not r:
                        lcd.display([(1,"Printing",0,"white"), (2,"Failed!",0,"red"),(3,"Printer is",0,"white"), (4,"Off!",0,"red") ], 24)
                        time.sleep(2)
                    self.state_index = 0
                    lcd.show_menu("Test Finished", ["Summary", "Power Off", "Re-Print"])
                    


# show message on screen
# updating EEPRON content
# show success message
# show summary of the test
# show message uploading 
# show success message
def main():
    # show final test result
    #initialize LCD and Keypad
    e2p = EEPROM()
    data, filename = e2p.read_json()
    print(data)
    # add date time field to summary json file
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    summary = {"timedate": date_time}
    if data.get("version") == "V1":
        if data.get('keypad', {}).get('test_result') and \
            data.get('lcd', {}).get('test_result') and \
            data.get('led', {}).get('test_result') and \
            data.get('eeprom', {}).get('test_result'):
            summary["test_result"] = True
            lcd.display([(1,"All Tests",0,"white"), (2,"Passed!",0,"green"), (3,chr(56),1,"green")], 24)
            time.sleep(2)
        else:
            summary["test_result"] = False
            lcd.display([(1,"Some Tests",0,"white"), (2,"Failed!",0,"red"), (3,chr(50),1,"red")], 24)
            time.sleep(2)
    elif data.get("version") == "V2":
        if data.get('keypad', {}).get('test_result') and \
            data.get("lcd",{}).get("test_result") and \
            data.get("led",{}).get("test_result") and \
            data.get("eeprom",{}).get("test_result") and \
            data.get("speakers",{}).get("test_result") and \
            data.get("microphones",{}).get("test_result") and \
            data.get("ambient",{}).get("test_result") and \
            data.get("temperature",{}).get("test_result") and \
            data.get("infrared",{}).get("test_result"): 
            summary["test_result"] = True
            lcd.display([(1,"All Tests",0,"white"), (2,"Passed!",0,"green"), (3,chr(56),1,"green")], 24)
            time.sleep(2)
        else:
            lcd.display([(1,"Some Tests",0,"white"), (2,"Failed!",0,"red"), (3,chr(50),1,"red")], 24)
            time.sleep(2)
            summary["test_result"] = False
    else: 
        lcd.display([(1,"No Valid",0,"white"), (2,"Version!",0,"red"), (3,chr(50),1,"red")], 23)
        time.sleep(2)
        summary["test_result"] = False
    lcd.display([(1,"Updating",0,"white"), (2,"EEPROM",0,"white"), (3,"Content...", 0,"white")], 25)
    print(summary)
    e2p.update_json(summary)
    ##########################################
    # update eeprom content 
    e2p.update_eeprom()
    # upload json file
    # if upload fails show error message
    # show summary of the test
    S = state_machine()
    if e2p.serial_number:
        with open( JSON_PATH + e2p.serial_number + ".json", "r") as f:
            S.data = json.load(f) # for showing summary on LCD
            temp_filename = JSON_PATH + e2p.serial_number + ".json"
            object_filename = e2p.serial_number + ".json"
            f.close()
            SN = e2p.serial_number 
    else:
        with open(JSON_PATH + "test_summary.json", "r") as f:
            S.data = json.load(f)
            temp_filename = JSON_PATH + "test_summary.json"
            object_filename = "summary_" + now.strftime("%Y%m%d-%H%M%S") + ".json"
            f.close()
            SN = "NO SERIAL#"
    num_of_retries = 4
    attempts = 0
    upload_result = False
    while attempts < num_of_retries:
        try:
            if attempts == 0:
                lcd.display([(1,"Uploading File",0,"white"), (2,object_filename,0,"green")], 15)
            else:
                lcd.display([(1,"Upload Failed",0,"white"), (2,"Trying Again...",0,"white"), (3, "Retry No: " + str(attempts),0,"red"), (4,temp_filename,0,"white") ], 16)
            upload_result  = upload_file(temp_filename, bucket_name, object_name=object_filename)
            if upload_result == True:
                attempts = num_of_retries + 1
            time.sleep(1)
            print("upload result is " + str(upload_result))
        except Exception as e:
            print(e)
            attempts += 1
            print("File upload Failed!")
    if upload_result:
        lcd.display([(1,"File Upload",0,"white"), (2,"Suceeded",0,"green"), (3,chr(56),1,"green") ], 25)
        print("File upload succeeded!")
    else:
        lcd.display([(1,"File Upload",0,"white"), (2,"Failed",0,"red"), (3,chr(50),1,"red") ], 25)
        print("File upload failed!")
    # print label through label printer
    lcd.display([(1,"Printing",0,"white"), (2,"The Label...",0,"green")], 25)
    S.label_info = {"serial_number": SN, "test_result": summary["test_result"], "test_date": date_time}
    r = print_label(S.label_info['serial_number'], 
                    S.label_info['test_result'],
                    S.label_info['test_date'])
    if not r:
        lcd.display([(1,"Printing",0,"white"), (2,"Failed!",0,"red"),(3,"Printer is",0,"white"), (4,"Off!",0,"red") ], 24)
    time.sleep(1)
    # show serial number
    # show prompt to show summary, power off, or re-print
    lcd.show_menu("Test Finished", ["Summary", "Power Off", "Re-Print"])
    while (S.state_index != 3): # check state machine state 
        time.sleep(1)
    # print(S.test_result)
    # if S.test_result:
    #     sys.exit(0)
    # else:
    #     sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
