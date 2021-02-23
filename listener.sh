#!/bin/sh
# listener.sh
# navigate to project directory, set path, start controller daemon

cd /home/pi/O-grow
sudo python3 detect_db_events.py

