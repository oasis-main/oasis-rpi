#import shell modules
import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/grow-ctrl')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

#import package modules
from time import sleep
import RPi.GPIO as GPIO
import serial
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT
import signal
import json

#communicating with firebase
import requests
import json

#dealing with specific times of the day
import datetime

#Initialize Oasis:
print("Initializing...")

#Load Model
with open('/home/pi/device_state.json') as d:
    device_state = json.load(d) #get device state
d.close()

with open('/home/pi/hardware_config.json') as h:
    hardware_config = json.load(h) #get hardware state
h.close()
print("Loaded state.")

#Launch Serial Port
ser_out = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser_out.flush()
print("Started serial communication.")

#check for connection
print("Checking for connection...")
try:

    #call connection
    prin("Call FireBase verification function HERE")

    #write device state as connectd if successful
    with open('/home/pi/device_state.json', 'r+') as d:
        device_state = json.load(d)
        device_state['connected'] = "1"
        d.seek(0) # <--- should reset file position to the begi$
        json.dump(device_state, d)
        d.truncate() # remove remaining part
    d.close()
    print("Device is connected to the Oasis Network")

except:

    #Write state as not connected
    with open('/home/pi/device_state.json', 'r+') as d:
        device_state = json.load(d)
        device_state['connected'] = "0"
        d.seek(0) # <--- should reset file position to the begi$
        json.dump(device_state, d)
        d.truncate() # remove remaining part
    d.close()
    print("Could not connect to Oasis Network")

#Case for when the device boots in Access Point Mode
with open('/home/pi/device_state.json') as d: #it is important to refresh the state for any operation after a change
    device_state = json.load(d) #get device state
d.close()

if device_state["AccessPoint"] == "1":

    print("Access Point Mode enabled")

    #set LEDstatus = "connectWifi"
    with open('/home/pi/device_state.json', 'r+') as d:
        device_state = json.load(d)
        device_state['LEDstatus'] = "connectWifi"
        d.seek(0) # <--- should reset file position to the begi$
        json.dump(device_state, d)
        d.truncate() # remove remaining part
    d.close()

    #launch server subprocess to accept credentials over Oasis wifi network
    server_process = Popen('sudo python3 /home/pi/grow-ctrl/oasis_server.py', shell=True)
    output, error = server_process.communicate()
    if server_process.returncode != 0:
        print("Failure " + str(server_process.returncode)+ " " +str(output)++str(error))


#Otherwise, run in Interface mode
else:
    print("Interface Mode enabled")

    #if the device is supposed to be running
    if device_state["running"] == "1":

        #launch sensingfeedback main
        sensingfeedback_process = Popen(['python3', '/home/pi/grow-ctrl/sensingfeedback_v1.11.py', 'main'], stdout=PIPE, stdin=PIPE, stderr=PIPE)

        if device_state["connected"] == "1": #if connected
            #send LEDmode = "connectedRunning"
            with open('/home/pi/device_state.json', 'r+') as d:
                device_state = json.load(d)
                device_state['LEDstatus'] = "connectedRunning"
                d.seek(0) # <--- should reset file position to the begi$
                json.dump(device_state, d)
                d.truncate() # remove remaining part
            d.close()
        else: #if not connected
            #send LEDmode = "islandRunning"
            with open('/home/pi/device_state.json', 'r+') as d:
                device_state = json.load(d)
                device_state['LEDstatus'] = "islandRunning"
                d.seek(0)
                json.dump(device_state, d)
                d.truncate()
            d.close()
        print("launched grow-ctrl main")

    else:

        #launch sensing-feedback subprocess in daemon mode
        sensingfeedback_process = Popen(['python3', '/home/pi/grow-ctrl/sensingfeedback_v1.11.py', 'daemon'], stdout=PIPE, stdin=PIPE, stderr=PIPE)


        if device_state["connected"] == "1":
            with open('/home/pi/device_state.json', 'r+') as d:
                device_state = json.load(d)
                device_state['LEDstatus'] = "connectedIdle"
                d.seek(0) # <--- should reset file position to the begi$
                json.dump(device_state, d)
                d.truncate() # remove remaining part
            d.close()

        else:
            with open('/home/pi/device_state.json', 'r+') as d:
                device_state = json.load(d)
                device_state['LEDstatus'] = "islandIdle"
                d.seek(0) # <--- should reset file position to the begi$
                json.dump(device_state, d)
                d.truncate() # remove remaining part
            d.close()

        print("launched grow-ctrl daemon")

    #setup GPIO
    GPIO.setmode(GPIO.BCM)

    #Set button pins
    StartButton = hardware_config["buttonGPIOmap"]["startStop"]
    ConnectButton = hardware_config["buttonGPIOmap"]["connectInternet"]
    WaterButton = hardware_config["buttonGPIOmap"]["runWater"]

    #set watering EPIO
    WaterElement = hardware_config["actuatorGPIOmap"]["wateringElement"] #watering aparatus

    #Setup buttons
    GPIO.setup(StartButton, GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ConnectButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(WaterButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(WaterElement, GPIO.OUT) #GPIO setup
    GPIO.output(WaterElement, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

    try:

       while True:
            with open('/home/pi/device_state.json') as d:
                device_state = json.load(d)
            d.close()

            sbutton_state = GPIO.input(StartButton) #Start Button

            if sbutton_state == 0:
                print("you hit the start button")

                if device_state["running"] == "1":

                    #set running state to off = 0
                    with open('/home/pi/device_state.json', 'r+') as d:
                        device_state = json.load(d)
                        device_state['running'] = "0" # <--- add `id` value.
                        d.seek(0) # <--- should reset file position to the beginning.
                        json.dump(device_state, d)
                        d.truncate() # remove remaining part
                    d.close()
                    #Kill sensingfeedback_main, launch daemon
                    try:
                        sensingfeedback_process.kill() #if it is running, kill it and launch the daemon
                        sensingfeedback_process.wait()
                        sensingfeedback_process = Popen(['python3', '/home/pi/grow-ctrl/sensingfeedback_v1.11.py', 'daemon'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
                        print("sensingfeedback daemon mode activated")
                    except:
                        print("sensingfeedback_process not running")

                    #Switch LED to idle mode
                    with open('/home/pi/device_state.json') as d:
                        device_state = json.load(d)
                    d.close()
                    if device_state["connected"] == "1":
                        with open('/home/pi/device_state.json', 'r+') as d:
                            device_state = json.load(d)
                            device_state['LEDstatus'] = "connectedIdle"
                            d.seek(0) # <--- should reset file position to the begi$
                            json.dump(device_state, d)
                            d.truncate() # remove remaining part
                        d.close()
                    else:
                        with open('/home/pi/device_state.json', 'r+') as d:
                            device_state = json.load(d)
                            device_state['LEDstatus'] = "islandIdle"
                            d.seek(0) # <--- should reset file position to the$
                            json.dump(device_state, d)
                            d.truncate() # remove remaining part
                        d.close()
                else:

                    #set running state to on = 1
                    with open('/home/pi/device_state.json', 'r+') as d:
                        device_state = json.load(d)
                        device_state['running'] = "1" # <--- update model
                        d.seek(0) # <--- should reset file position to the beginning.
                        json.dump(device_state, d)
                        d.truncate() # remove remaining part
                    d.close()

                    #try kill daemon & start sensingfeedback main
                    try:
                        sensingfeedback_process.kill() #kill daemon, launch main
                        sensingfeedback_process.wait()
                        sensingfeedback_process = Popen(['python3', '/home/pi/grow-ctrl/sensingfeedback_v1.11.py', 'main'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
                        print("sensingfeedback main activated")
                    except:
                        print("sensing_feedback process not running")


                    #Switch LED to running mode
                    with open('/home/pi/device_state.json') as d:
                        device_state = json.load(d)
                    d.close()
                    if device_state["connected"] == "1":
                        with open('/home/pi/device_state.json', 'r+') as d:
                            device_state= json.load(d)
                            device_state['LEDstatus'] = "connectedRunning"
                            d.seek(0) # <--- should reset file position to the$
                            json.dump(device_state, d)
                            d.truncate() # remove remaining part
                        d.close()
                    else:
                        with open('/home/pi/device_state.json', 'r+') as d:
                            device_state = json.load(d)
                            device_state['LEDstatus'] = "islandRunning"
                            d.seek(0) # <--- should reset file position to the$
                            json.dump(device_state, d)
                            d.truncate() # remove remaining part
                        d.close()
                sleep(1) #give the buttons some time to breathe

            cbutton_state = GPIO.input(ConnectButton) #Connect Button

            if cbutton_state == 0:
                #send message
                print("you hit the connect button")

                #disable WiFi, enable AP, update state, reboot
                os.system("sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf")
                os.system("sudo cp /etc/dnsmasq_AP.conf /etc/dnsmasq.conf")
                os.system("sudo systemctl enable hostapd")

                #set AccessPoint state to "1" before rebooting
                with open('/home/pi/device_state.json', 'r+') as d:
                    device_state = json.load(d)
                    device_state['AccessPoint'] = "1" # <--- add `id` value.
                    d.seek(0) # <--- should reset file position to the beginning.
                    json.dump(device_state, d)
                    d.truncate() # remove remaining part
                d.close()
                #exit
                os.system("sudo systemctl reboot")

            wbutton_state = GPIO.input(WaterButton) #Water Button

            if wbutton_state == 0:

               #turn on the pump
               GPIO.output(WaterElement, GPIO.HIGH)
               #wait 60 seconds
               sleep(60)
               #turn off the pump
               GPIO.output(WaterElement, GPIO.LOW)

            #get device_state
            with open('/home/pi/device_state.json') as d:
                device_state = json.load(d)
            d.close()

            #write the LED config to serial port

            #write "off" or write status depending on ToD + settings
            now = datetime.datetime.now()
            HoD = now.hour

            if int(device_state["LEDtimeon"]) < int(device_state['LEDtimeoff']):
                if HoD >= int(device_state["LEDtimeon"]) and HoD < int(device_state["LEDtimeoff"]):
                    ser_out.write(bytes(str(device_state["LEDstatus"]+"\n"), 'utf-8')) #write status
                if HoD < int(device_state["LEDtimeon"]) or HoD >= int(device["LEDtimeoff"]):
                    ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
            if int(device_state["LEDtimeon"]) >int(device_state["LEDtimeoff"]):
                if HoD >=  int(device_state["LEDtimeon"]) or HoD < int(device_state["LEDtimeoff"]):
                    ser_out.write(bytes(str(device_state["LEDstatus"]+"\n"), 'utf-8')) #write status
                if HoD < int(device_state["LEDtimeon"]) and  HoD >= int(device_state["LEDtimeoff"]):
                    ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
            if int(device_state["LEDtimeon"]) == int(device_state["LEDtimeoff"]):
                ser_out.write(bytes(str(device_state["LEDstatus"]+"\n"), 'utf-8')) #write status

            #debug main subprocess
            print(sensingfeedback_process.stderr.read(20))
            sleep(.25)
    except(KeyboardInterrupt):
        GPIO.cleanup()
