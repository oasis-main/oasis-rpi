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
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal
import json

#communicating with firebase
import requests
import json

#dealing with specific times of the day
import time
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

with open('/home/pi/access_config.json') as a:
    access_config = json.load(a) #get hardware state
a.close()

print("Loaded state.")

#Launch Serial Port
ser_out = serial.Serial('/dev/ttyUSB0', 9600)
ser_out.flush()
print("Started serial communication.")

#check for connection
print("Checking for connection...")
try:

    #call connection
    print("FireBase verification...")
    #must define wak, refresh_token
    refresh_token = access_config['refresh_token']
    wak = access_config['wak']
    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
    refresh_req = requests.post(refresh_url, data=refresh_payload)
    #print(refresh_req)

    #write device state as connected if successful
    with open('/home/pi/device_state.json', 'r+') as d:
        device_state = json.load(d)
        device_state['connected'] = "1"
        d.seek(0) # <--- should reset file position to the begi$
        json.dump(device_state, d)
        d.truncate() # remove remaining part
    d.close()
    print("Device is connected to the Oasis Network")

   #write device state as connected if successful
    with open('/home/pi/access_config.json', 'r+') as a:
        access_config = json.load(a)
        access_config['id_token'] = refresh_req.json()['id_token']
        access_config['local_id'] = refresh_req.json()['user_id']
        a.seek(0) # <--- should reset file position to the begi$
        json.dump(access_config, a)
        d.truncate() # remove remaining part
    d.close()
    print("Obtained fresh credentials")

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

        #launch grow_ctrl main
        grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'main'])

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
        grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'daemon'])

        if device_state["connected"] == "1":
            with open('/home/pi/device_state.json', 'r+') as d:
                device_state = json.load(d)
                device_state['LEDstatus'] = "connectedIdle"
                d.seek(0)
                json.dump(device_state, d)
                d.truncate() # remove remaining part
            d.close()

        else:
            with open('/home/pi/device_state.json', 'r+') as d:
                device_state = json.load(d)
                device_state['LEDstatus'] = "islandIdle"
                d.seek(0)
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

    #start the clock for timimg data exchanges with Arduino LED
    start = time.time()

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
                    #Kill grow_ctrl_main, launch daemon
                    try:
                        grow_ctrl_process.kill() #if it is running, kill it and launch the daemon
                        grow_ctrl_process.wait()
                        grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'daemon'])
                        print("grow_ctrl daemon mode activated")
                    except:
                        print("grow_ctrl_process not running")

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

                    #try kill daemon & start grow_ctrl main
                    try:
                        grow_ctrl_process.kill() #kill daemon, launch main
                        grow_ctrl_process.wait()
                        grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'main'])
                        print("grow_ctrl main activated")
                    except:
                        print("grow_ctrl process not running")


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

            #exchange data with arduino for LED after set time elapses
            if time.time() - start > 5:
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

                #restart the clock
                start = time.time()

    except(KeyboardInterrupt):
        GPIO.cleanup()
