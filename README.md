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

## Testing EEPROM ROM
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







