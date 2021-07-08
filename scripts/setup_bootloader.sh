#!/bin/sh -e

sudo chmod +w /etc/rc.local
sudo sed -ie "/^fi/a python3.9 /home/pi/oasis-grow/controller.py &" /etc/rc.local
