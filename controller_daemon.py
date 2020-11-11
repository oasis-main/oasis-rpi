import os
import os.path
import sys

#set proper path for modules
#print(sys.path)
sys.path.append('/home/pi/grow-ctrl')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

from time import sleep
import RPi.GPIO as GPIO
import serial
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT
import signal
import json

#get device_state
with open('/home/pi/device_state.json') as d:
    device_state = json.load(d)

#get hardware config
with open('/home/pi/hardware_config.json') as h:
  hardware_config = json.load(h)


if device_state["AccessPoint"] == '1':
    #launch server subprocess
    server_process = Popen(['sudo', 'python3', '/home/pi/grow-ctrl/oasis_server.py'], stdout=PIPE, stdin=PIPE, stderr=PIPE)

    #setup GPIO
    GPIO.setmode(GPIO.BCM)
    #Set Button pin
    Button = 27
    #Setup Button and LED
    GPIO.setup(Button,GPIO.IN,pull_up_down=GPIO.PUD_UP)

    try:
        while True:
            button_state = GPIO.input(Button)
            if button_state == 0:
                #Shut Down Server Disable AP, enable WiFis, reboot
                server_process.kill()
                server_process.wait()
                os.system("sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf")
                os.system("sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf")
                os.system("sudo systemctl disable hostapd")
                #set AccessPoint state to "0" before rebooting
                with open('/home/pi/device_state.json', 'r+') as f:
                    data = json.load(f)
                    data['AccessPoint'] = "0" # <--- add `id` value.
                    f.seek(0) # <--- should reset file position to the beginning.
                    json.dump(data, f)
                    f.truncate() # remove remaining part
                #exit
                os.system("sudo systemctl reboot")

    except(KeyboardInterrupt):
        GPIO.cleanup()

else:
    #setup GPIO
    GPIO.setmode(GPIO.BCM)
    #Set Button pins
    ConnectButton = 27
    WaterButton = hardware_config["actuatorGPIOmap"]["wateringElement"] #watering aparatus
    #Setup Button and LED
    GPIO.setup(ConnectButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(WaterButton, GPIO.OUT) #GPIO setup
    GPIO.output(WaterButton, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

    try:
        while True:
            cbutton_state = GPIO.input(ConnectButton)
            if cbutton_state == 0:
                #sisable WiFi, enable AP, update state, reboot
                os.system("sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf")
                os.system("sudo cp /etc/dnsmasq_AP.conf /etc/dnsmasq.conf")
                os.system("sudo systemctl enable hostapd")
                #set AccessPoint state to "1" before rebooting
                with open('/home/pi/device_state.json', 'r+') as f:
                    data = json.load(f)
                    data['AccessPoint'] = "1" # <--- add `id` value.
                    f.seek(0) # <--- should reset file position to the beginning.
                    json.dump(data, f)
                    f.truncate() # remove remaining part
                #exit
                os.system("sudo systemctl reboot")

            wbutton_state = GPIO.input(WaterButton)
            if wbutton_state == 0:
                #turn on the pump
                GPIO.output(WaterButton, GPIO.HIGH)
            else:
                GPIO.output(WaterButton, GPIO.LOW)
    except(KeyboardInterrupt):
        GPIO.cleanup()
