UBO_HOME=/home/pi/ubo
export PATH=$PATH:/home/pi/.local/bin

python3 -m pip install --upgrade pip
pip3 install --upgrade pip
pip3 install -r $UBO_HOME/setup/requirements.txt

#######################################
# Install SeeedStudio for speakers
######################################
/bin/bash $UBO_HOME/setup/install_seeedstudio.sh

#######################################
# Install EEPROM tools
######################################
/bin/bash $UBO_HOME/setup/install_eeprom.sh

#######################################
# Install Infra Red tools
######################################
sudo apt install ir-keytable 

#######################################
# Update config files
######################################
sudo cp $UBO_HOME/boot/config.txt /boot/config.txt
sudo cp $UBO_HOME/etc/modprobe.d/snd-blacklist.conf /etc/modprobe.d/snd-blacklist.conf
#######################################
# Add systemd services
######################################
sudo cp $UBO_HOME/etc/systemd/system/hardware-test.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hardware-test
sudo systemctl restart hardware-test
