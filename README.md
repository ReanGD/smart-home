Create virtual env for arch
---------------------------

```bash
pacaur -S swig
cd ~/projects/venv
virtualenv smart-home
source smart-home/bin/activate
pip3 install pyaudio pocketsphinx webrtcvad soco respeaker protobuf

git clone https://github.com/Kitt-AI/snowboy.git ~/tmp/snowboy
cd ~/tmp/snowboy
sed -i -e "s|-lf77blas -lcblas -llapack -latlas|-lcblas|g" -e 's/ -shared/ -Wl,-O1,--as-needed\0/g' "swig/Python3/Makefile"
python setup.py build
python setup.py install
rm -rf ~/tmp/snowboy

./generate_proto.sh

deactivate
```

pyusb
-----

```bash
pip3 install pyusb

udevadm info -a -p $(udevadm info -q path -n /dev/snd/by-id/usb-SeeedStudio_ReSpeaker_MicArray_UAC2.0-00)

sudo nano /etc/udev/rules.d/99-garmin.rules

SUBSYSTEM=="usb", ATTR{idVendor}=="2886", ATTR{idProduct}=="0007", MODE="666"

sudo udevadm control --reload
```

reconnect mic
protocol: https://github.com/Fuhua-Chen/ReSpeaker-Microphone-Array-HID-tool

other
-----

```bash
pip3 install pysoundcard SpeechRecognition
```