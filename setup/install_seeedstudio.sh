aplay -l | grep seeed &> /dev/null
if [ $? == 0 ]; then
   echo "SeeedStudio already installed"
else
   echo "installing seeedstudio, restarted needed after"
   # git clone https://github.com/respeaker/seeed-voicecard.git
   git clone https://github.com/HinTak/seeed-voicecard
   cd seeed-voicecard
   git pull
   git checkout v6.0
   sudo ./install.sh
   cd ..
fi
