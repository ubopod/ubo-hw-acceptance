#!/bin/bash

print_result () {
	if [ $2 -eq 0 ]; then
	   echo -e "\e[39m$1 \t\t\t\t\t [ \e[32mOK \e[39m]"
	else
	   echo -e "\e[39m$1 \t\t\t\t\t [ \e[91mFAIL \e[39m]"
	fi
}

# update files if there's an update on github master branch.
git checkout master
git pull --no-rebase https://github.com/ubopod/ubo-hw-acceptance.git
# Install pip packages if requirements.txt is updated
su -c 'pip install -r ../../setup/requirements.txt' pi

export PYTHONPATH=/home/pi/.local/lib/python3.9/site-packages/

#read -p "Press any key for EEPROM test" -n1 -s
echo -e "\n\n========= Starting EEPROM Test ============"
PYTHONPATH=$PYTHONPATH python3 test_eeprom.py
eeprom=$?

#read -p "Press any key to scan I2C bus" -n1 -s
echo -e "\n\n========= Starting I2C Bus Scan ============"
PYTHONPATH=$PYTHONPATH python3 scan_i2c.py
i2c=$?

#read -p "Press any key for LCD test" -n1 -s
echo -e "\n\n========= Starting LCD Test ============"
PYTHONPATH=$PYTHONPATH python3 test_lcd.py
lcd=$?

#read -p "Press any key for buttons test" -n1 -s
echo -e "\n\n========= Startin Buttons Test ============"
PYTHONPATH=$PYTHONPATH python3 test_buttons.py
buttons=$?


if [ $buttons -eq 0 ] && [ $lcd -eq 0 ] 
then
	#read -p "Press any key for LED test" -n1 -s
	echo -e "\n\n========= Starting LED Test ============"
	PYTHONPATH=$PYTHONPATH python3 test_led.py
	led=$?
	# if does not have sensors, IR, and audio (V1 SKU), then skip those tests
	if [ $i2c -eq 65 ] 
	then
		#read -p "Press any key for light sensor test" -n1 -s
		echo -e "\n\n========= Starting Light Sensor Test ============"
		PYTHONPATH=$PYTHONPATH python3 test_ambient.py
		ambient=$?

		#read -p "Press any key for temperature test" -n1 -s
		echo -e "\n\n========= Starting Temparture Sensor Test ============"
		PYTHONPATH=$PYTHONPATH python3 test_temperature.py
		temp=$?

		echo -e "\n\n========= Starting speaker Test ============"
		PYTHONPATH=$PYTHONPATH python3 test_speakers.py
		speaker=$?

		echo -e "\n\n========= Starting microphone Test ============"
		PYTHONPATH=$PYTHONPATH python3 test_microphone.py
		mic=$?

		echo -e "\n\n========= Starting Infrared Test ============"
		PYTHONPATH=$PYTHONPATH python3 test_ir.py
		ir=$?
	fi

fi
 
echo -e "\n\n======== Test Results  ============"
# print_result "Device     " $device
print_result "EEPROM      " $eeprom
print_result "LCD        " $lcd
print_result "Keypad    " $buttons
print_result "LED        " $led
print_result "Light Sensor  " $ambient 
print_result "Temperature" $temp
print_result "Speaker    " $speaker
print_result "Microhpne  " $mic
print_result "InfraRed   " $ir

echo -e "\n\n========= Uploading Summary Data ============"
## Upload to S3 Bucket
PYTHONPATH=$PYTHONPATH python3 test_summarize.py
