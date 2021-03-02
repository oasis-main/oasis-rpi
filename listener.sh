#!/bin/sh
# listener.sh
# navigate to project directory, set path, start controller daemon

cd /home/pi/grow-ctrl
sudo python3 detect_db_events.py

