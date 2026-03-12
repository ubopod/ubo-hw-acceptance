UBO_HOME=/home/pi/ubo
export PATH=$PATH:/home/pi/.local/bin

curl -LsSf https://astral.sh/uv/install.sh | sh

sudo apt install -y python3-gpiozero

uv sync --directory $UBO_HOME

#######################################
# Install WM8960 audio driver
######################################
/bin/bash $UBO_HOME/setup/install_wm8960.sh

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
