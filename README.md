pip3 install pysoundcard

pip3 install SpeechRecognition

pip3 install pyaudio

pacaur -S swig

pacaur -S python-snowboy

pip3 install pyaudio respeaker webrtcvad pocketsphinx

pip3 install requests. soco

pyusb
-----

pip3 install pyusb

udevadm info -a -p $(udevadm info -q path -n /dev/snd/by-id/usb-SeeedStudio_ReSpeaker_MicArray_UAC2.0-00)

sudo nano /etc/udev/rules.d/99-garmin.rules

SUBSYSTEM=="usb", ATTR{idVendor}=="2886", ATTR{idProduct}=="0007", MODE="666"

sudo udevadm control --reload

reconnect mic

protocol: https://github.com/Fuhua-Chen/ReSpeaker-Microphone-Array-HID-tool