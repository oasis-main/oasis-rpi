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
import RPi.GPIO as GPIO
import serial
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal

#communicating with firebase
import requests

#json management
import json

#dealing with specific time
import time
from time import sleep
import datetime

#declare state variables
device_state = None #describes the current state of the system
hardware_config = None #holds hardware I/O setting & pin #s
access_config = None #contains credentials for connecting to firebase

#declare process management variables
ser_out = None #object for writing to the microcontroller via serial
grow_ctrl_process = None #variable to launch & manage the grow controller
WaterElement = None #holds GPIO object for running the watering aparatus

#declare UI variables
StartButton = None #holds GPIO object for starting and stopping grow_ctrl process
ConnectButton = None #holds GPIO object for connecting device to internet
WaterButton = None #holds GPIO object for triggering the watering aparatus

#loads device state, hardware, and access configurations
def load_state(): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, hardware_config, access_config

    with open("/home/pi/device_state.json") as d:
        device_state = json.load(d) #get device state
    d.close()

    with open("/home/pi/hardware_config.json") as h:
        hardware_config = json.load(h) #get hardware state
    h.close()

    with open("/home/pi/access_config.json") as a:
        access_config = json.load(a) #get access state
    a.close()

    #print("Loaded state")

#modifies a firebase variable
def patch_firebase(field,value): #Depends on: load_state(),'requests','json'; Modifies: database['field'], state variables
    load_state()
    data = json.dumps({field: value})
    url = "https://oasis-1757f.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)

#save key values to .json
def write_state(path,field,value): #Depends on: load_state(), patch_firebase, 'json'; Modifies: path
    load_state() #get connection status

    if device_state["connected"] == "1": #write state to cloud
        try:
            patch_firebase(field,value)
        except:
            pass

    with open(path, "r+") as x: #write state to local files
        data = json.load(x)
        data[field] = value
        x.seek(0)
        json.dump(data, x)
        x.truncate()
    x.close()

#attempts connection to microcontroller
def start_serial(): #Depends on:'serial'; Modifies: ser_out
    global ser_out

    try:
        try:
            ser_out = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
            ser_out.flush()
            print("Started serial communication with Arduino Nano.")
        except:
            ser_out = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
            ser_out.flush()
            print("Started serial communication with Arduino Uno.")
    except Exception as e:
        ser_out = None
        print("Serial connection not found")

#gets new refresh token from firebase
def get_refresh_token(web_api_key,email,password): #Depends on: 'requests', 'json', write_state; Modifies: None
    sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + web_api_key
    sign_in_payload = json.dumps({"email": email, "password": password, "returnSecureToken": "true"})
    r = requests.post(sign_in_url, sign_in_payload)
    data = json.loads(r.content)
    return data["refreshToken"]

#get local_id and id_token from firebase
def get_local_credentials(refresh_token): #Depends on: load_state(), write_state(), 'requests'; Modifies: state variables,  access_config.json
    #load state so we can use access credentials
    load_state()
    wak = access_config["wak"]
    email = access_config["e"]
    password = access_config["p"]

    #get local credentials
    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
    refresh_req = requests.post(refresh_url, data=refresh_payload)

    #write local credentials to access config
    write_state("/home/pi/access_config.json","id_token",refresh_req.json()["id_token"])
    write_state("/home/pi/access_config.json","local_id",refresh_req.json()["user_id"])

    print("Obtained local credentials")

#check if the device is waiting to be added to firebase, if it is then add it, otherwise skip
def check_new_device(): #depends on: ;modifies:
    load_state()
    if device_state["connected"] == "0" and device_state["new_device"] == "1":
        my_data = "{\"" + access_config["device_name"] + '\":{"connected":"1","running":"0","LEDstatus":"off","AccessPoint":"0","LEDtimeon":"0","LEDtimeoff":"0","awaiting_update":"0","targetT":"70","targetH":"90","targetL":"on","LtimeOn":"8","LtimeOff":"20","lightInterval":"60","cameraInterval":"3600","waterMode":"off","waterDuration":"15","waterInterval":"3600","temp":"N/A","hum":"N/A","waterLow":"0","new_image":"0","new_device":"0"}}'

        #add box data to firebase
        url = "https://oasis-1757f.firebaseio.com/"+access_config["local_id"]+".json?auth="+access_config["id_token"]
        post_request = requests.patch(url,my_data)

        write_state("/home/pi/device_state.json","new_device","0")
        print("New device added to firebase")

#connects system to firebase
def connect_firebase(): #depends on: load_state(), write_state(), patch_firebase(), 'requests'; Modifies: access_config.json, device_state.json
    #load state so we can use access credentials
    load_state()
    wak = access_config["wak"]
    email = access_config["e"]
    password = access_config["p"]

    print("Checking for connection...")

    try:
        print("FireBase verification...")

        #fetch refresh token
        refresh_token = get_refresh_token(wak, email, password)

        #fetch refresh token and save to access_config
        write_state("/home/pi/access_config.json","refresh_token", refresh_token)

        #bring in the refresh token for use further down
        load_state()
        refresh_token = access_config["refresh_token"]
        print("Obtained refresh token")

        #fetch a new id_token & local_id
        get_local_credentials(refresh_token)

        #check if new device
        check_new_device()

        #let firebase know the connection was successful
        patch_firebase("connected","1")

        #update the device state to "connected"
        write_state('/home/pi/device_state.json',"connected","1")
        print("Device is connected to the Oasis Network")

    except Exception as e:
        print(e) #display error
        #write state as not connected
        write_state("/home/pi/device_state.json","connected","0")
        print("Could not connect to Oasis Network")

#checks for available updates, executes if connected & idle, waits for completion
def check_updates(): #depends on: load_state(),'subproceess', update.py; modifies: system code, state variables
    load_state()
    if device_state["connected"] == "1" and device_state["running"] == "0" and device_state["awaiting_update"] == "1": #replicated in the main loop
        #launch update.py and wait to complete
        update_process = Popen("sudo python3 /home/pi/grow-ctrl/update.py", shell=True)
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))

#setup buttons for the main program interface
def setup_button_interface(): #depends on: load_state(), 'RPi.GPIO'; modifies: StartButton, ConnectButton, WaterButton, state variables
    global StartButton, ConnectButton, WaterButton
    #specify gpio pin number mode
    GPIO.setmode(GPIO.BCM)

    #get hardware configuration
    load_state()

    #set button pins
    StartButton = hardware_config["buttonGPIOmap"]["startStop"]
    ConnectButton = hardware_config["buttonGPIOmap"]["connectInternet"]
    WaterButton = hardware_config["buttonGPIOmap"]["runWater"]

    #Setup buttons
    GPIO.setup(StartButton, GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ConnectButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(WaterButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#setup restart button for Access Point Button
def setup_button_AP(): #Depends on: load_state(), 'RPi.GPIO'; Modifies: ConnectButton, state variables
    global ConnectButton
    GPIO.setmode(GPIO.BCM)

    #get hardware configuration
    load_state()

    #set button pins
    ConnectButton = hardware_config["buttonGPIOmap"]["connectInternet"]

    #Setup buttons
    GPIO.setup(ConnectButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#gets the state of a button (returns 1 if not pressed, 0 if pressed)
def get_button_state(button): #Depends on: RPi.GPIO; Modifies: None
    state = GPIO.input(button)
    return state

#reconfigures network interface, tells system to boot with Access Point, restarts
def enable_AP(): #Depends on: write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should be launched on next controller startup
    write_state("/home/pi/device_state.json","AccessPoint","1")

    #disable WiFi, enable AP, reboot
    config_ap_dhcpcd = Popen("sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf", shell = True)
    config_ap_dhcpcd.wait()
    config_ap_dns = Popen("sudo cp /etc/dnsmasq_AP.conf /etc/dnsmasq.conf", shell = True)
    config_ap_dns.wait()
    enable_hostapd = Popen("sudo systemctl enable hostapd", shell = True)
    enable_hostapd.wait()
    systemctl_reboot = Popen("sudo systemctl reboot", shell = True)

#reconfigures network interface, tells system to boot with WiF, restarts
def enable_WiFi(): #Depends on: write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should not be launched on next controller startup
    write_state("/home/pi/device_state.json","AccessPoint","0")

    #disable WiFi, enable AP, reboot
    config_wifi_dchpcd = Popen("sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf", shell = True)
    config_wifi_dchpcd.wait()
    config_wifi_dns = Popen("sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf", shell = True)
    config_wifi_dns.wait()
    disable_hostapd = Popen("sudo systemctl disable hostapd", shell = True)
    disable_hostapd.wait()
    systemctl_reboot = Popen("sudo systemctl reboot", shell = True)

#checks whether system is booting in Access Point Mode, launches connection script if so
def check_AP(): #Depends on: 'subprocess', oasis_server.py, setup_button_AP(); Modifies: state_variables, 'ser_out', device_state.json
    global ser_out
    load_state()
    if device_state["AccessPoint"] == "1":
        #launch server subprocess to accept credentials over Oasis wifi network, does not wait
        server_process = Popen("sudo python3 /home/pi/grow-ctrl/oasis_server.py", shell=True)
        print("Access Point Mode enabled")

        setup_button_AP()

        if ser_out is not None:
            #set LEDstatus = "connectWifi"
            write_state("/home/pi/device_state.json","LEDstatus","connectWifi")
            load_state()
            #write LED state to seriaL
            while True: #place the "exit button" here to leave connection mode
                ser_out.write(bytes(str(device_state["LEDstatus"]+"\n"), "utf-8"))
                cbutton_state = get_button_state(ConnectButton)
                if cbutton_state == 0:
                    server_process.kill()
                    server_process.wait()
                    enable_WiFi()
        else:
            while True:
                cbutton_state = get_button_state(ConnectButton)
                if cbutton_state == 0:
                    server_process.kill()
                    server_process.wait()
                    enable_WiFi()

#check if grow_ctrl is supposed to be running, launch it if so. Do nothing if not
def setup_growctrl_process(): #Depends on: load_state(), write_state(), 'subprocess'; Modifies: grow_ctrl_process, state_variables, device_state.json
    global grow_ctrl_process
    load_state()

    #if the device is supposed to be running
    if device_state["running"] == "1":

        #launch grow_ctrl main
        grow_ctrl_process = Popen(["sudo", "python3", "/home/pi/grow-ctrl/grow_ctrl.py", "main"])

        if device_state["connected"] == "1": #if connected
            #LEDmode = "connectedRunning"
            write_state("/home/pi/device_state.json","LEDstatus","connectedRunning")
        else: #if not connected
            write_state("/home/pi/device_state.json","LEDstatus","islandRunning")

        print("launched grow-ctrl")

    else:

        #launch sensing-feedback subprocess in daemon mode
        grow_ctrl_process = Popen(["sudo", "python3", "/home/pi/grow-ctrl/grow_ctrl.py", "daemon"])

        if device_state["connected"] == "1": #if connected
            #LEDmode = "connectedIdle"
            write_state("/home/pi/device_state.json","LEDstatus","connectedIdle")
        else: #if not connected
            write_state('/home/pi/device_state.json',"LEDstatus","islandIdle")

        print("grow_ctrl not launched")

#checks if growctrl should be running, starts it if so, kills it otherwise
def check_growctrl_running(): #Depends on: load_state(), write_state(), 'subprocess'; Modifies: grow_ctrl_process, state variables, device_state.json
    global grow_ctrl_process
    load_state()

    #if the device is supposed to be running
    if device_state["running"] == "1":

        poll_grow_ctrl = grow_ctrl_process.poll() #check if grow_ctrl process is running
        if poll_grow_ctrl is not None: #if it is not running
            #launch it
            grow_ctrl_process = Popen(["sudo", "python3", "/home/pi/grow-ctrl/grow_ctrl.py", "main"])
            print("launched grow-ctrl")

            if device_state["connected"] == "1": #if connected
                #send LEDmode = "connectedRunning"
                write_state("/home/pi/device_state.json","LEDstatus","connectedRunning")
            else: #if not connected
                #send LEDmode = "islandRunning"
                write_state("/home/pi/device_state.json","LEDstatus","islandRunning")

    else:

        poll_grow_ctrl = grow_ctrl_process.poll() #check if grow_ctrl process is running
        if poll_grow_ctrl is None: #if it is running
            try: #try to kill it
                grow_ctrl_process.kill()
                grow_ctrl_process.wait()
                print("grow_ctrl_process deactivated")
            except:
                pass

            if device_state["connected"] == "1": #if connected
                #send LEDmode = "connectedIdle"
                write_state("/home/pi/device_state.json","LEDstatus","connectedIdle")
            else: #if not connected
                #send LEDmode = "islandIdle"
                write_state("/home/pi/device_state.json","LEDstatus","islandIdle")

#checks if growctrl is running, kills it if so, starts it otherwise
def switch_growctrl_running(): #Depends on: load_state(), write_state(), patch_firebase(), 'subprocess'; Modifies: device_state.json, state_variables
    load_state()

    #if the device is set to running
    if device_state["running"] == "1":
        #set running state to off = 0
        write_state("/home/pi/device_state.json","running","0")

    #if not set to running
    else:
        #set running state to on = 1
        write_state("/home/pi/device_state.json","running","1")

#sets up the watering aparatus
def setup_water(): #Depends on: load_state(), 'RPi.GPIO'; Modifies: WaterElement
    global WaterElement
    #get hardware configuration
    load_state()

    #set watering GPIO
    WaterElement = hardware_config["actuatorGPIOmap"]["wateringElement"] #watering aparatus
    GPIO.setwarnings(False)
    GPIO.setup(WaterElement, GPIO.OUT) #GPIO setup
    GPIO.output(WaterElement, GPIO.LOW) #relay open = GPIO.LOW, closed = GPIO.HIGH

#runs the watering aparatus for a supplied interval
def run_water(interval): #Depends on: 'RPi.GPIO'; Modifies: WaterElement
    global WaterElement
    #turn on the pump
    GPIO.output(WaterElement, GPIO.HIGH)
    #wait 60 seconds
    sleep(interval)
    #turn off the pump
    GPIO.output(WaterElement, GPIO.LOW)

#updates the state of the LED, serial must be set up,
def update_LED(): #Depends on: load_state(), 'datetime'; Modifies: ser_out
    global ser_out
    load_state()

    #write "off" or write status depending on ToD + settings
    now = datetime.datetime.now()
    HoD = now.hour

    if ser_out is not None:
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
    else:
        #print("no serial connection, cannot update LED view")
        pass

#copies the listener's buffer into the main model, avoiding overwrite errors from cloud + controller
def sync_cloud_state(): #Depends on: 'json','subprocess'

    try:
        with open("/home/pi/device_state_buffer.json") as d_buff: #verify that the cloud is not currently writing
            device_state_buffer = json.load(d_buff)
        d_buff.close()
        copy_device_state_buffer = Popen("sudo cp /home/pi/device_state_buffer.json /home/pi/device_state.json", shell = True)
        copy_device_state_buffer.wait()
    except Exception as e:
        print("concurrent writing collision: device_state")
        print(e)
        pass

    try:
        with open("/home/pi/grow_params_buffer.json") as g_buff:
            grow_params_buffer = json.load(g_buff) #verify that the cloud is not currently writing
        g_buff.close()
        copy_grow_params_buffer = Popen("sudo cp /home/pi/grow_params_buffer.json /home/pi/grow_params.json", shell = True)
        copy_grow_params_buffer.wait()
    except Exception as e:
        print("concurrent writing collision: grow_params")
        print(e)
        pass

if __name__ == '__main__':

    #Initialize Oasis:
    print("Initializing...")
    time.sleep(10)
    load_state()
    start_serial()
    check_AP()
    connect_firebase()
    check_updates()
    setup_growctrl_process()
    setup_button_interface()
    setup_water()

    #start the clock for timing credential refresh &  data exchanges with LED
    led_timer = time.time()
    token_timer = time.time()

    try:
        while True:
            load_state() #refresh the state variables

            check_updates() #check if the machine needs to be update

            if device_state["connected"] == "1":
                if time.time() - token_timer > 600: #refresh the local credentials every 10 min (600s)
                    token_timer = time.time()
                    get_local_credentials(access_config["refresh_token"])

            check_growctrl_running() #check if growctrl is supposed to be running

            sbutton_state = get_button_state(StartButton) #Start Button
            if sbutton_state == 0:
                print("User pressed the start/stop button")
                switch_growctrl_running() #turn growctrl on/off
                time.sleep(1)

            cbutton_state = get_button_state(ConnectButton) #Connect Button
            if cbutton_state == 0:
                print("User pressed the connect button")
                enable_AP() #launch access point and reboot
                time.sleep(1)

            wbutton_state = get_button_state(WaterButton) #Water Button
            if wbutton_state == 0:
                run_water(60) #run the water for 60 seconds
                time.sleep(1)

            if time.time() - led_timer > 5: #send data to LED ever 5s
                update_LED()
                led_timer = time.time()

            if device_state["connected"] == "1": #get data from cloud
                sync_cloud_state()

    except(KeyboardInterrupt):
        GPIO.cleanup()
