#!/bin/sh -e

sudo chmod +w /etc/rc.local
sudo sed -ie "/^fi/a python3 /home/pi/oasis-grow/main.py &" /etc/rc.local
