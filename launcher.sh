#!/bin/sh
# launcher.sh
# navigate to project directory, set path, start controller daemon
export PYTHONPATH="/home/pi/grow-ctrl:/usr/lib/python37.zip:/usr/lib/python3.7:/usr/lib/python3.7/lib-dynload:/home/pi/.local/lib/python3.7/site-packages:/usr/local/lib/python3.7/dist-packages:/usr/lib/python3/dist-packages"
cd /home/pi/grow-ctrl
sudo python3 controller_daemon.py

