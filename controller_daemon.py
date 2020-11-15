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

#get device_state
with open('/home/pi/device_state.json') as d:
    device_state = json.load(d)

#get hardware config
with open('/home/pi/hardware_config.json') as h:
    hardware_config = json.load(h)

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.flush()

#check for connection
print("Checking for connection...")
try:
    print("Call firebase verification function") #mispell the print statement to 
    connected = True
    print("Device is connected to the Oasis Network")
except:
    connected = False
    print("Could not connect to Oasis Network")

#Detect mode for  wifi
if device_state["AccessPoint"] == "1":
    #send LEDmode = "connectWifi"
    with open('/home/pi/device_state.json', 'r+') as r:
        data = json.load(r)
        data['LEDstatus'] = "connectWifi"
        r.seek(0) # <--- should reset file position to the begi$
        json.dump(data, r)
        r.truncate() # remove remaining part
    #launch server subprocess
    #server_process = Popen('sudo python3 /home/pi/grow-ctrl/oasis_server.py', stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
    #output, error = server_process.communicate()
    #if server_process.returncode != 0:
    #    print("Failure " + str(server_process.returncode)+ " " +str(output)++str(error))
    #setup GPIO
    GPIO.setmode(GPIO.BCM)
    #Set Button pin
    Button = hardware_config["buttonGPIOmap"]["connectInternet"]
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
            #update LED
            with open('/home/pi/device_state.json') as d:
                device_state = json.load(d)
            ser.flush()
            ser.write(bytes(str(device_state["LEDstatus"])+"\n", 'utf-8'))
    except(KeyboardInterrupt):
        GPIO.cleanup()

#If not in wifi mode, run normal interface loop
else:

    if device_state["running"] == "1":
        #launch sensing-feedback loop normally
        #launch server subprocess
        #server_process = Popen(['python3', '/home/pi/grow-ctrl/sensingfeedback_v1.11.py', 'main'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        #output, error = server_process.communicate()
        #if server_process.returncode != 0:
        #    print("Failure " + str(server_process.returncode)+ " " +str(output)++str(error))
        if connected == True:
            #send LEDmode = "connectedRunning"
            with open('/home/pi/device_state.json', 'r+') as r:
                data = json.load(r)
                data['LEDstatus'] = "connectedRunning"
                r.seek(0) # <--- should reset file position to the begi$
                json.dump(data, r)
                r.truncate() # remove remaining part
        if connected == False:
            #send LEDmode = "islndRunning"
            with open('/home/pi/device_state.json', 'r+') as r:
                data = json.load(r)
                data['LEDstatus'] = "islandRunning"
                r.seek(0) # <--- should reset file position to the begi$
                json.dump(data, r)
                r.truncate() # remove remaining part
        print("launched grow-ctrl main")
    else:
        #launch sensing-feedback subprocess in daemon mode
        #sensingfeedback_process = Popen(['python3', '/home/pi/grow-ctrl/sensingfeedback_v1.11.py', 'daemon'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        #output, error = sensingfeedback_process.communicate()
        #if sensingfeedback_process.returncode != 0:
        #    print("Failure " + str(sensingfeedback_process.returncode)+ " " +str(output)++str(error))
        if connected == True:
            with open('/home/pi/device_state.json', 'r+') as r:
                data = json.load(r)
                data['LEDstatus'] = "connectedIdle"
                r.seek(0) # <--- should reset file position to the begi$
                json.dump(data, r)
                r.truncate() # remove remaining part
        if connected == False:
            with open('/home/pi/device_state.json', 'r+') as r:
                data = json.load(r)
                data['LEDstatus'] = "islandIdle"
                r.seek(0) # <--- should reset file position to the begi$
                json.dump(data, r)
                r.truncate() # remove remaining part
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
            sbutton_state = GPIO.input(StartButton)
            with open('/home/pi/device_state.json') as d:
                device_state = json.load(d)
            if sbutton_state == 0:
                print("you hit the start button")
                if device_state["running"] == "1":
                    #set running state to off = 0
                    with open('/home/pi/device_state.json', 'r+') as r:
                        data = json.load(r)
                        data['running'] = "0" # <--- add `id` value.
                        r.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, r)
                        r.truncate() # remove remaining part
                    #Kill sensingfeedback process
                    
                    #Switch LED to idle mode
                    if connected == True:
                        with open('/home/pi/device_state.json', 'r+') as r:
                            data = json.load(r)
                            data['LEDstatus'] = "connectedIdle"
                            r.seek(0) # <--- should reset file position to the begi$
                            json.dump(data, r)
                            r.truncate() # remove remaining part
                    if connected == False:
                        with open('/home/pi/device_state.json', 'r+') as r:
                            data = json.load(r)
                            data['LEDstatus'] = "islandIdle"
                            r.seek(0) # <--- should reset file position to the$
                            json.dump(data, r)
                            r.truncate() # remove remaining part
                else:
                    #set running state to on = 1
                    with open('/home/pi/device_state.json', 'r+') as r:
                        data = json.load(r)
                        data['running'] = "1" # <--- update model
                        r.seek(0) # <--- should reset file position to the beginning.
                        json.dump(data, r)
                        r.truncate() # remove remaining part
                    #start sensingfeedback process
                    #Switch LED to idle mode
                    if connected == True:
                        with open('/home/pi/device_state.json', 'r+') as r:
                            data = json.load(r)
                            data['LEDstatus'] = "connectedRunning"
                            r.seek(0) # <--- should reset file position to the$
                            json.dump(data, r)
                            r.truncate() # remove remaining part
                    if connected == False:
                        with open('/home/pi/device_state.json', 'r+') as r:
                            data = json.load(r)
                            data['LEDstatus'] = "islandRunning"
                            r.seek(0) # <--- should reset file position to the$
                            json.dump(data, r)
                            r.truncate() # remove remaining part

                sleep(1) #give the buttons some time to breathe

            cbutton_state = GPIO.input(ConnectButton)
            if cbutton_state == 0:
                #send message
                print("you hit the connect button")
                #disable WiFi, enable AP, update state, reboot
                os.system("sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf")
                os.system("sudo cp /etc/dnsmasq_AP.conf /etc/dnsmasq.conf")
                os.system("sudo systemctl enable hostapd")

                #set AccessPoint state to "1" before rebooting
                with open('/home/pi/device_state.json', 'r+') as c:
                    data = json.load(c)
                    data['AccessPoint'] = "1" # <--- add `id` value.
                    c.seek(0) # <--- should reset file position to the beginning.
                    json.dump(data, c)
                    c.truncate() # remove remaining part
                #exit
                os.system("sudo systemctl reboot")

            wbutton_state = GPIO.input(WaterButton)
            if wbutton_state == 0:
                #turn on the pump
                GPIO.output(WaterElement, GPIO.HIGH)
            else:
                GPIO.output(WaterElement, GPIO.LOW)

            #get device_state
            with open('/home/pi/device_state.json') as d:
                device_state = json.load(d)


            ser.flush()
            ser.write(bytes(str(device_state["LEDstatus"]+"\n"), 'utf-8'))

    except(KeyboardInterrupt):
        GPIO.cleanup()
