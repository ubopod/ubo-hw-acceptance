# Ubo Hardware Acceptance Tests
This repo constrains test scripts for hardware acceptance tests that are performed during manufacturing by the factory. 

Note: The test results get uploaded to S3 bucket at the end, but due to security reasons AWS keys have been removed from this script. If you wish to have the test resultuploaded to your own S3 service, replace keys with valid keys.

## Setup

Update your system and clone this repository 

```
sudo apt update  
sudo apt upgrade  
git clone https://github.com/ubopod/ubo-hw-acceptance.git
```

rename working directory

`mv ./ubo-hw-acceptance /home/pi/ubo`

If you end up using a different directory name or location, make sure you change the first line in `install.sh` script to reflact that:

`UBO_HOME=/home/pi/ubo` in `setup/install.sh` 

## Install

Run install script to setup everything

```
cd setup/  
bash install.sh
```

## Reboot
`sudo reboot`

# What does it do?

The main script `test.sh` runs a suite of individual tests which are managed by seperate python scripts that function as standalone tests. The python scripts can be excecuted seperately to test only a certain functions. In the following section, we provide a brief overview of each test step, its purpos, and things to looh out for.

## Testing EEPROM ROM

When the test starts, it first run 'tests/hw_acceptance/test_eeprom.py' script that tests the EEPROM and write some initializtion data on it. To test the EEPROM, it first checks it the device is detected on the correct I2C bus address. Then, it reads the content to see if the EEPROM has been tested before and contains valid information. If so, it terminates the process and the scripts proceeds to next step. If the EEPROM does not contain recognizable information and it has not been programmed previously, it writes all zeros to the memory (erases the content) and reads back the content to make sure it is all zero.

Valid EEPROM entry must contain the following information:



## Scanning for I2C devices
## Testing LCD
## Testing Keypad
## Testing LED Ring
## Testing Light Sensor
## Testing Temperature Sensor
## Testing Speakers
## Testing Microphones
## Testing IR Transmitter and Receiver
## Writing test results on EEPRON
## Uploading test results to S3
## Priting QA Label with serial number







