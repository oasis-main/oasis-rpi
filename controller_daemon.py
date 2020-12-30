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
time.sleep(20)

#Load Model
with open('/home/pi/device_state.json') as d:
    device_state = json.load(d) #get device state
d.close()

with open('/home/pi/hardware_config.json') as h:
    hardware_config = json.load(h) #get hardware state
h.close()

with open('/home/pi/access_config.json') as a:
    access_config = json.load(a) #get access state
a.close()

print("Loaded state.")

#Launch Serial Port
ser_out = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser_out.flush()
print("Started serial communication.")

#check for connection
print("Checking for connection...")
try:

    #call connection
    print("FireBase verification...")

    #GET NEW REFESH TOKEN
    def getNewRefreshToken(web_api_key,email,password):
        sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + web_api_key
        sign_in_payload = json.dumps({"email": email, "password": password, "returnSecureToken": "true"})
        r = requests.post(sign_in_url, sign_in_payload)
        data = json.loads(r.content)
        return data['refreshToken']

    wak = access_config['wak']
    email = access_config['e']
    password = access_config['p']

    #write credentials to access config if successful
    with open('/home/pi/access_config.json', 'r+') as a:
        access_config = json.load(a)
        access_config['refresh_token'] = getNewRefreshToken(wak, email, password)
        a.seek(0) # <--- should reset file position to the begi$
        json.dump(access_config, a)
        a.truncate() # remove remaining part
    a.close()
    print("Obtained refresh token")

    with open('/home/pi/access_config.json') as a:
        access_config = json.load(a) #get access state
    a.close()

    #must define wak, refresh_token
    refresh_token = access_config['refresh_token']
    wak = access_config['wak']
    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
    refresh_req = requests.post(refresh_url, data=refresh_payload)
    #print(refresh_req)

    #write credentials to access config if successful
    with open('/home/pi/access_config.json', 'r+') as a:
        access_config = json.load(a)
        access_config['id_token'] = refresh_req.json()['id_token']
        access_config['local_id'] = refresh_req.json()['user_id']
        a.seek(0) # <--- should reset file position to the begi$
        json.dump(access_config, a)
        a.truncate() # remove remaining part
    a.close()
    print("Obtained local credentials")

    #let firebase know the connection was successful
    with open('/home/pi/access_config.json', "r+") as a:
        access_config = json.load(a)
        id_token = access_config['id_token']
        local_id = access_config['local_id']
    a.close()

    data = json.dumps({"connected": "1"})
    url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
    result = requests.patch(url,data)

    #write device state as connected if successful
    with open('/home/pi/device_state.json', 'r+') as d:
        device_state = json.load(d)
        device_state['connected'] = "1"
        d.seek(0) # <--- should reset file position to the begi$
        json.dump(device_state, d)
        d.truncate() # remove remaining part
    d.close()
    print("Device is connected to the Oasis Network")

except Exception as e:
    print(e)
    #sys.exit()
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

if device_state["connected"] == "1" and device_state["running"] == "0" and device_state["awaiting_update"] == "1": #replicated in the main loop
    #launch update.py and wait to complete
    update_process = Popen('sudo python3 /home/pi/grow-ctrl/update.py', shell=True)
    output, error = update_process.communicate()
    if update_process.returncode != 0:
        print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))

#Case, check whether the program should boot in Access Point Mode
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
    ser_out.write(bytes(str(device_state["LEDstatus"]+"\n"), 'utf-8')) #write status
    server_process = Popen('sudo python3 /home/pi/grow-ctrl/oasis_server.py', shell=True)
    while True:
        ser_out.write(bytes(str(device_state["LEDstatus"]+"\n"), 'utf-8')) #write status

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
        print("launched grow-ctrl")

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

        print("grow_ctrl not launched")

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
    token_timer = time.time()

    try:

       while True:
            with open('/home/pi/device_state.json') as d:
                device_state = json.load(d)
            d.close()

            with open('/home/pi/access_config.json') as a:
                access_config = json.load(a)
            a.close()

            #let firebase know the connection was successful
            with open('/home/pi/access_config.json', "r+") as a:
                access_config = json.load(a)
                id_token = access_config['id_token']
                local_id = access_config['local_id']
            a.close()

            if device_state["connected"] == "1" and device_state["running"] == "0" and device_state["awaiting_update"] == "1": #replicated in the main loop
                #launch update.py and wait to complete
                update_process = Popen('sudo python3 /home/pi/grow-ctrl/update.py', shell=True)
                output, error = update_process.communicate()
                if update_process.returncode != 0:
                    print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))

            if device_state["connected"] == "1":
                #insert try/except statement to handle expired refresh token

                if time.time() - token_timer > 600:
                    refresh_token = access_config['refresh_token']
                    wak = access_config['wak']
                    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
                    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
                    refresh_req = requests.post(refresh_url, data=refresh_payload)

                    #write credentials to access config if successful
                    with open('/home/pi/access_config.json', 'r+') as a:
                        access_config = json.load(a)
                        access_config['id_token'] = refresh_req.json()['id_token']
                        access_config['local_id'] = refresh_req.json()['user_id']
                        a.seek(0) # <--- should reset file position
                        json.dump(access_config, a)
                        a.truncate() # remove remaining part
                    a.close()
                    print("Obtained fresh credentials")

            #if the device is supposed to be running
            if device_state["running"] == "1":

                poll_grow_ctrl = grow_ctrl_process.poll() #check if process is running
                if poll_grow_ctrl is not None:
                    #launch grow_ctrl main
                    grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'main'])
                    print("launched grow-ctrl")

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

            else:
                #try to kill grow_ctrl process
                poll_grow_ctrl = grow_ctrl_process.poll() #heat
                if poll_grow_ctrl is None:
                    try:
                        grow_ctrl_process.kill() #if it is running, kill it and launch the daemon
                        grow_ctrl_process.wait()
                        #grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'daemon'])
                        print("grow_ctrl_process deactivated")
                    except:
                        pass

                #launch sensing-feedback subprocess in daemon mode
                #grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'daemon'])

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

            sbutton_state = GPIO.input(StartButton) #Start Button

            if sbutton_state == 0:
                print("you hit the start button")

                if device_state["running"] == "1":

                    data = json.dumps({"running": "0"})
                    url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
                    result = requests.patch(url,data)

                    #set running state to off = 0
                    with open('/home/pi/device_state.json', 'r+') as d:
                        device_state = json.load(d)
                        device_state['running'] = "0" # <--- add `id` value.
                        d.seek(0) # <--- should reset file position to the beginning.
                        json.dump(device_state, d)
                        d.truncate() # remove remaining part
                    d.close()

                    #try to kill grow_ctrl process
                    try:
                        grow_ctrl_process.kill() #if it is running, kill it and launch the daemon
                        grow_ctrl_process.wait()
                        #grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'daemon'])
                        print("grow_ctrl_process deactivated")
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

                    data = json.dumps({"running": "1"})
                    url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
                    result = requests.patch(url,data)

                    #set running state to on = 1
                    with open('/home/pi/device_state.json', 'r+') as d:
                        device_state = json.load(d)
                        device_state['running'] = "1" # <--- update model
                        d.seek(0) # <--- should reset file position to the beginning.
                        json.dump(device_state, d)
                        d.truncate() # remove remaining part
                    d.close()

                    #start grow_ctrl
                    try:
                        #grow_ctrl_process.kill() #kill daemon, launch main
                        #grow_ctrl_process.wait()
                        grow_ctrl_process = Popen(['python3', '/home/pi/grow-ctrl/grow_ctrl.py', 'main'])
                        print("grow_ctrl process activated")
                    except:
                        print("failed to start grow_ctrl")

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
                config_ap_dhcpcd = Popen("sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf", shell = True)
                config_ap_dhcpcd.wait()
                config_ap_dns = Popen("sudo cp /etc/dnsmasq_AP.conf /etc/dnsmasq.conf", shell = True)
                config_ap_dns.wait()
                enable_hostapd = Popen("sudo systemctl enable hostapd", shell = True)
                enable_hostapd.wait()

                data = json.dumps({"AccessPoint": "1"})
                url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
                result = requests.patch(url,data)

                #set AccessPoint state to "1" before rebooting
                with open('/home/pi/device_state.json', 'r+') as d:
                    device_state = json.load(d)
                    device_state['AccessPoint'] = "1" # <--- add `id` value.
                    d.seek(0) # <--- should reset file position to the beginning.
                    json.dump(device_state, d)
                    d.truncate() # remove remaining part
                d.close()
                #exit
                systemctl_reboot = Popen("sudo systemctl reboot", shell = True)

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
                    if HoD < int(device_state["LEDtimeon"]) or HoD >= int(device_state["LEDtimeoff"]):
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
