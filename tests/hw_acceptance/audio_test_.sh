#############################
## Testing Audio with Alsa
#############################
echo -e "\n* Testing Speakers ... "
# test left channel with alsa
echo -e "You must hear the phrase LEFT CHANNEL"
aplay -D hw:3,0 left.wav
#test right channel with aplay
echo -e "You must hear the phrase RIGHT CHANNEL"
aplay -D hw:3,0 right.wav
# test recording audio
echo -e "Now say something to be recorded"
arecord -D hw:3,0 --duration=5 --file-type=wav --format=S16_LE --rate=16000 --channels=2 mic_test.wav
# separate audio channels
# split channels into two files
ffmpeg -i mic_test.wav -map_channel 0.0.0 mic_test_left.wav -map_channel 0.0.1 mic_test_right.wav
# playback left channel of recorded audio 
aplay -D plughw:CARD=seeed2micvoicec,DEV=0 -c 1 -f S16_LE mic_test_left.wav
# playback right channel of recorded audio 
aplay -D plughw:CARD=seeed2micvoicec,DEV=0 -c 1 -f S16_LE mic_test_right.wav
# Please note that for some weird reason aplay -D hw:3,0 does not work for the
# last two files and only works for first file. However, aplay -D plughw:CARD=seeed2micvoicec,DEV=0
# works!!!