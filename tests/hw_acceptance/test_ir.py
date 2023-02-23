# IR test script
import subprocess
import os
import sys
import time
up_dir = os.path.dirname(os.path.abspath(__file__))+'/../../'
sys.path.append(up_dir)
from lcd import LCD as LCD
#from ubo_keypad import KEYPAD as KEYPAD
from ubo_keypad import * # Might have to revisit this form of import
from eeprom import *

result = False
#initialize LCD and Keypad
lcd = LCD()
lcd.set_lcd_present(1)

#subprocess.run(["ls", "-l"])
#subprocess.run(["sudo", "ir-keytable"])
#subprocess.run(["sudo", "ir-keytable", "-c", "-p", "all", "-t", "-s", "rc1"], shell=True, timeout=10, stdin=None, stdout=None, stderr=None)
#f = open("test_ir_codes.txt", "w")
# p1 = subprocess.Popen(["sudo", "ir-keytable", "-c", "-p", "all", "-t", "-s", "rc0"], stdout=f)
# p1 = subprocess.Popen('sudo ir_send.sh', shell=True)

def send_ir_command(r=5):
    for i in range(r):
        degree = 360*((i+1)/r)
        # print(degree)
        lcd.progress_wheel("Testing IR ...",degree,"green")
        #show progress wheel
        os.system("sudo ir-ctl -S sony12:0x10015")
        time.sleep(0.1)
        print("sending IR command...")

def main():
    lcd.display([(1,"Starting",0,"white"), (2,"Infrared (IR)",0,"white"), (3,"Test", 0,"white")], 25)
    e2p = EEPROM()
    # show message that IR test is initiating 
    # find gpio_ir_recv device
    # try different rc devices
    for i in range(5):
        dev = "rc" + str(i)
        print("Trying device: " + dev)
        p1 = subprocess.Popen('sudo stdbuf -i0 -o0 -e0 ir-keytable -c -p all -t -s ' + dev + ' > test_ir_codes.txt', shell=True)
        time.sleep(1)
        returncode = p1.poll()
        print(returncode)
        if returncode == None:
            break
    send_ir_command(6)
    # example of piping stdout
    # p1 = subprocess.Popen(["dmesg"], stdout=subprocess.PIPE)
    # p2 = subprocess.Popen(["grep", "0xbf01"], stdin=p1.stdout, stdout=subprocess.PIPE)

    # kill process with sudo
    print("Process spawned with PID: %s" % p1.pid)
    pgid = os.getpgid(p1.pid)
    try:
        subprocess.check_output("sudo kill {}".format(p1.pid), shell=True)
        subprocess.check_output("sudo kill {}".format(p1.pid+2), shell=True)
    except:
        pass
    # try:
    #     #p1.wait(timeout=2)
    #     p1.kill()
    # except subprocess.TimeoutExpired:
    #     pass
    # open and analyze the file
    f = open("test_ir_codes.txt", "r")
    if '0x10015' in f.read():
        print("IR Test Passed!!")
        lcd.display([(1,"IR Test",0,"white"), (2, "Result:", 0, "white"), (3,"Passed",0,"green"), (4,chr(56),1,"green")], 25)
        result = True
    else:
        print("IR Test Failed!!")
        lcd.display([(1,"IR Test",0,"white"), (2, "Result:", 0, "white"), (3,"Failed",0,"red"), (4,chr(50),1,"red")], 25)
        result = False
    f.close()
    # "infrared": {
    #     "receiver": "tsop75238",
    #     "test_result": true,
    #     "test_report": {
    #             "sony12": true,
    #             "nec": true
    #         }
    # }
    summary = {"infrared":{}}
    summary["infrared"]["receiver"] = "tsop75238"
    summary["infrared"]["test_result"] = result
    summary["infrared"]["test_report"] = {"sony12": True}
    e2p.update_json(summary)
    if result:
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
