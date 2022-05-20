#This is the program root, main.py. Run this file from the command line, in cron, through systemd, or in rc.local(preferred).

#Tips:
# Use the -b when installing with 'source ./master_setup.sh" to setup the bootloader ie. 'source ./master_setup.sh -b'

#import shell modules
import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')
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
import multiprocessing
import signal

#communicating with firebase
import requests

#json management
import json

#dealing with specific time
import time
from time import sleep
import datetime

#import other oasis packages
from utils import reset_model
from utils import concurrent_state as cs
from imaging import camera_element



#declare process management variables
listener = None
ser_out = None #object for writing to the microcontroller via serial
core_process = None #variable to launch & manage the grow controller

#declare UI variables
start_stop_button = None #holds GPIO object for starting and stopping core process
connect_internet_button = None #holds GPIO object for connecting device to internet
action_button = None #holds GPIO object for triggering the desired action

#attempts connection to microcontroller
def start_serial(): #Depends on:'serial'; Modifies: ser_out
    global ser_out

    if cs.feature_toggles["onboard_led"] == "1":
        pass
    else:
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
            #print(str(e))
            ser_out = None
            print("Serial connection not found")

#gets new refresh token from firebase
def get_refresh_token(web_api_key,email,password): #Depends on: 'requests', 'json', cs.write_state; Modifies: None
    sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + web_api_key
    sign_in_payload = json.dumps({"email": email, "password": password, "returnSecureToken": "true"})
    r = requests.post(sign_in_url, sign_in_payload)
    data = json.loads(r.content)
    return data["refreshToken"]

#get local_id and id_token from firebase
def get_local_credentials(refresh_token): #Depends on: cs.load_state(), cs.write_state(), 'requests'; Modifies: state variables,  cs.access_config.json
    #load state so we can use access credentials
    cs.load_state()
    wak = cs.access_config["wak"]
    email = cs.access_config["e"]
    password = cs.access_config["p"]

    #get local credentials
    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
    refresh_req = requests.post(refresh_url, data=refresh_payload)

    #write local credentials to access config
    cs.write_state("/home/pi/oasis-grow/configs/access_config.json","id_token",refresh_req.json()["id_token"])
    cs.write_state("/home/pi/oasis-grow/configs/access_config.json","local_id",refresh_req.json()["user_id"])

    print("Obtained local credentials")

#connects system to firebase
def connect_firebase(): #depends on: cs.load_state(), cs.write_state(), cs.patch_firebase(), 'requests'; Modifies: access_config.json, device_state.json
    
    def try_connect():
   
        #load state so we can use access credentials
        cs.load_state()
        wak = cs.access_config["wak"]
        email = cs.access_config["e"]
        password = cs.access_config["p"]

        print("Checking for connection...")

        try:
            print("FireBase verification...")

            #fetch refresh token
            refresh_token = get_refresh_token(wak, email, password)

            #fetch refresh token and save to access_config
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","refresh_token", refresh_token)

            #bring in the refresh token for use further down
            cs.load_state()
            refresh_token = cs.access_config["refresh_token"]
            print("Obtained refresh token")

            #fetch a new id_token & local_id
            get_local_credentials(refresh_token)

            #launch checks at network startup
            check_new_device()
            check_updates()
            check_deleted()

            #start listener to bring in db changes
            if cs.device_state["connected"] == "0":
                launch_listener()

            #update the device state to "connected"
            cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"connected","1")
            print("Device is connected over HTTPS to the Oasis Network")

            cs.load_state()
            
        except Exception as e:
            print(e) #display error
            #write state as not connected
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0")
            print("Could not establish an HTTPS connection to Oasis Network")

    time.sleep(15)
    connection_attempt = multiprocessing.Process(target = try_connect)
    connection_attempt.start()

#check if the device is waiting to be added to firebase, if it is then add it, otherwise skip
def check_new_device(): #depends on: modifies:
    cs.load_state()

    if cs.device_state["new_device"] == "1":

        #assemble data to initialize firebase
        setup_dict = {}
        setup_dict.update(cs.device_state)
        setup_dict.update(cs.device_params)
        setup_dict.update(cs.feature_toggles)
        setup_dict_named = {cs.access_config["device_name"] : setup_dict}
        my_data = json.dumps(setup_dict_named)
        #print(my_data)
        #print(type(my_data))

        #add box data to firebase
        url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+cs.access_config["local_id"]+".json?auth="+cs.access_config["id_token"]
        post_request = requests.patch(url,my_data)
        #print(post_request.ok)
        if post_request.ok:
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","new_device","0")
            print("New device added to firebase")
        else:
            print("Failed to add new device")

#checks for available updates, executes if connected & idle, waits for completion
def check_updates(): #depends on: cs.load_state(),'subproceess', update.py; modifies: system code, state variables
    cs.load_state()
    if cs.device_state["running"] == "0" and cs.device_state["awaiting_update"] == "1": #replicated in the main loop
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
    if cs.device_state["running"] == "1" and cs.device_state["awaiting_update"] == "1": #replicated in the main loop
        #flip running to 0        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1") #restore running
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
            
#launches a script to detect changes in the database
def launch_listener(): #depends on 'subprocess', modifies: state variables
    global listener
    listener = Popen(["python3", "/home/pi/oasis-grow/networking/detect_db_events.py"])

#deletes a box if the cloud is indicating that it should do so
def check_deleted():
    global listener
    cs.load_state()
    if cs.device_state["deleted"] == "1" and listener is not None:
        print("Removing device from Oasis Network...")
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        print("Database monitoring deactivated")
        reset_model.reset_nonhw_configs()
        print("Device has been reset to default configuration")
        systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])

#setup buttons for the main program interface
def setup_button_interface(): #depends on: cs.load_state(), 'RPi.GPIO'; modifies: start_stop_button, connect_internet_button, run_action_button, state variables
    global start_stop_button, connect_internet_button, action_button
    #specify gpio pin number mode
    GPIO.setmode(GPIO.BCM)

    #get hardware configuration
    cs.load_state()

    #set button pins
    start_stop_button = cs.hardware_config["button_gpio_map"]["start_stop_button"]
    connect_internet_button = cs.hardware_config["button_gpio_map"]["connect_internet_button"]
    action_button = cs.hardware_config["button_gpio_map"]["action_button"]

    #Setup buttons
    GPIO.setup(start_stop_button, GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(connect_internet_button,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(action_button,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#setup restart button for Access Point Button
def setup_button_AP(): #Depends on: cs.load_state(), 'RPi.GPIO'; Modifies: connect_internet_button, state variables
    global connect_internet_button
    GPIO.setmode(GPIO.BCM)

    #get hardware configuration
    cs.load_state()

    #set button pins
    connect_internet_button = cs.hardware_config["button_gpio_map"]["connect_internet_button"]

    #Setup buttons
    GPIO.setup(connect_internet_button,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#gets the state of a button (returns 1 if not pressed, 0 if pressed)
def get_button_state(button): #Depends on: RPi.GPIO; Modifies: None
    state = GPIO.input(button)
    return state

#reconfigures network interface, tells system to boot with Access Point, restarts
def enable_AP(): #Depends on: cs.write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should be launched on next controller startup
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","1")

    #disable WiFi, enable AP, reboot
    config_ap_dhcpcd = Popen(["sudo", "cp", "/etc/dhcpcd_AP.conf", "/etc/dhcpcd.conf"])
    config_ap_dhcpcd.wait()
    config_ap_dns = Popen(["sudo", "cp", "/etc/dnsmasq_AP.conf", "/etc/dnsmasq.conf"])
    config_ap_dns.wait()
    enable_hostapd = Popen(["sudo", "systemctl", "enable", "hostapd"])
    enable_hostapd.wait()
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])

#reconfigures network interface, tells system to boot with WiF, restarts
def enable_WiFi(): #Depends on: cs.write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should not be launched on next controller startup
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","0")

    #disable WiFi, enable AP, reboot
    config_wifi_dchpcd = Popen(["sudo", "cp", "/etc/dhcpcd_WiFi.conf", "/etc/dhcpcd.conf"])
    config_wifi_dchpcd.wait()
    config_wifi_dns = Popen(["sudo", "cp", "/etc/dnsmasq_WiFi.conf", "/etc/dnsmasq.conf"])
    config_wifi_dns.wait()
    disable_hostapd = Popen(["sudo", "systemctl", "disable", "hostapd"])
    disable_hostapd.wait()
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])

#checks whether system is booting in Access Point Mode, launches connection script if so
def check_AP(): #Depends on: 'subprocess', oasis_server.py, setup_button_AP(); Modifies: state_variables, 'ser_out', device_state.json
    global ser_out, connect_internet_button
    cs.load_state()
    if cs.device_state["access_point"] == "1":
        #launch server subprocess to accept credentials over Oasis wifi network, does not wait
        server_process = Popen(["sudo", "streamlit", "run", "/home/pi/oasis-grow/networking/oasis_setup.py", "--server.headless=true", "--server.port=80", "--server.address=192.168.4.1", "--server.enableCORS=false", "--server.enableWebsocketCompression=false"])
        print("Access Point Mode enabled")

        setup_button_AP()

        if ser_out is not None:
            #set led_status = "connectWifi"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","accepting_wifi_connection")
            cs.load_state()
            #write LED state to seriaL
            while True: #place the "exit button" here to leave connection mode
                ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), "utf-8"))
                cbutton_state = get_button_state(connect_internet_button)
                if cbutton_state == 0:
                    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle")
                    ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), "utf-8"))
                    server_process.terminate()
                    server_process.wait()
                    enable_WiFi()
                    time.sleep(1)
        else:
            while True:
                cbutton_state = get_button_state(connect_internet_button)
                if cbutton_state == 0:
                    server_process.terminate()
                    server_process.wait()
                    enable_WiFi()
                    time.sleep(1)

#check if core is supposed to be running, launch it if so. Do nothing if not
def setup_core_process(): #Depends on: cs.load_state(), cs.write_state(), 'subprocess'; Modifies: core_process, state_variables, device_state.json
    global core_process
    cs.load_state()

    #if the device is supposed to be running
    if cs.device_state["running"] == "1":

        #launch core main
        core_process = Popen(["python3", "/home/pi/oasis-grow/core/core.py", "main"])

        if cs.device_state["connected"] == "1": #if connected
            #LEDmode = "connected_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running")
        else: #if not connected
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running")

        print("launched grow controller")

    else:

        #launch sensing-feedback subprocess in daemon mode
        core_process = Popen(["python3", "/home/pi/oasis-grow/core/core.py", "daemon"])

        if cs.device_state["connected"] == "1": #if connected
            #LEDmode = "connected_idle"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle")
        else: #if not connected
            cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"led_status","offline_idle")

        print("grow controller not launched")

#checks in the the core process has been called from the command line
def cmd_line_args():
    try:
        if sys.argv[1] == "run":
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1")
            print("Command line argument set to run")
        if sys.argv[1] == "idle":
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")
            print("Command line argument set to idle")
    except Exception as e:
        print("Defaulting to last saved mode...")

#checks if core should be running, starts it if so, kills it otherwise
def check_core_running(): #Depends on: cs.load_state(), cs.write_state(), 'subprocess'; Modifies: core_process, state variables, device_state.json
    global core_process
    cs.load_state()

    #if the device is supposed to be running
    if cs.device_state["running"] == "1":

        poll_core = core_process.poll() #check if core process is running
        if poll_core is not None: #if it is not running
            #launch it
            core_process = Popen(["python3", "/home/pi/oasis-grow/core/core.py", "main"])
            print("launched grow-ctrl")

            if cs.device_state["connected"] == "1": #if connected
                #send LEDmode = "connected_running"
                cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running")
            else: #if not connected
                #send LEDmode = "offline_running"
                cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running")

    else:

        poll_core = core_process.poll() #check if core process is running
        if poll_core is None: #if it is running
            try: #try to kill it
                core_process.terminate()
                core_process.wait()
                print("core_process deactivated")
            except:
                pass

            if cs.device_state["connected"] == "1": #if connected
                #send LEDmode = "connected_idle"
                cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle")
            else: #if not connected
                #send LEDmode = "offline_idle"
                cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle")

#checks if core is running, kills it if so, starts it otherwise
def switch_core_running(): #Depends on: cs.load_state(), cs.write_state(), cs.patch_firebase(), 'subprocess'; Modifies: device_state.json, state_variables
    cs.load_state()

    #if the device is set to running
    if cs.device_state["running"] == "1":
        #set running state to off = 0
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")

    #if not set to running
    else:
        #set running state to on = 1
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1")

#sets up the watering aparatus
def setup_water(): #Depends on: cs.load_state(), 'RPi.GPIO'; Modifies: water_relay
    global water_relay
    #get hardware configuration
    cs.load_state()

    #set watering GPIO
    water_relay = cs.hardware_config["actuator_gpio_map"]["water_relay"] #watering aparatus
    GPIO.setwarnings(False)
    GPIO.setup(water_relay, GPIO.OUT) #GPIO setup
    GPIO.output(water_relay, GPIO.LOW) #relay open = GPIO.LOW, closed = GPIO.HIGH

#runs the watering aparatus for a supplied interval
def run_water(interval): #Depends on: 'RPi.GPIO'; Modifies: water_relay
    global water_relay
    #turn on the pump
    GPIO.output(water_relay, GPIO.HIGH)
    #wait 60 seconds
    sleep(interval)
    #turn off the pump
    GPIO.output(water_relay, GPIO.LOW)

#updates the state of the LED, serial must be set up,
def update_LED(): #Depends on: cs.load_state(), 'datetime'; Modifies: ser_out
    global ser_out
    cs.load_state()

    #write "off" or write status depending on ToD + settings
    now = datetime.datetime.now()
    HoD = now.hour

    if ser_out is not None:
        if int(cs.device_params["time_start_led"]) < int(cs.device_params["time_stop_led"]):
            if HoD >= int(cs.device_params["time_start_led"]) and HoD < int(cs.device_params["time_stop_led"]):
                ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(cs.device_params["time_start_led"]) or HoD >= int(cs.device_params["time_stop_led"]):
                ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.device_params["time_start_led"]) > int(cs.device_params["time_stop_led"]):
            if HoD >=  int(cs.device_params["time_start_led"]) or HoD < int(cs.device_params["time_stop_led"]):
                ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(cs.device_params["time_start_led"]) and  HoD >= int(cs.device_params["time_stop_led"]):
                ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.device_params["time_start_led"]) == int(cs.device_params["time_stop_led"]):
                ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), 'utf-8')) #write status
    else:
        #print("no serial connection, cannot update LED view")
        pass

def main_setup():

    #Initialize Oasis:
    print("Initializing...")
    cs.load_state()
    start_serial()
    check_AP()
    connect_firebase()

    #Check if command line set to run
    cmd_line_args()

    #launch core process
    setup_core_process()

    #Setup on-device interface
    setup_button_interface()
    
    if cs.feature_toggles["action_button"] == "1":
        if cs.feature_toggles["action_water"] == "1":
            setup_water()

    #start the clock for timing credential refresh &  data exchanges with LED
    led_timer = time.time()
    connect_timer = time.time()

    return led_timer, connect_timer

def main_loop(led_timer, connect_timer):
    
    try:
        while True:
            cs.load_state() #refresh the state variables

            if time.time() - connect_timer > 900:
                connect_firebase

            check_core_running() #check if core is supposed to be running

            sbutton_state = get_button_state(start_stop_button) #Start Button
            if sbutton_state == 0:
                print("User pressed the start/stop button")
                switch_core_running() #turn core on/off
                time.sleep(1)

            cbutton_state = get_button_state(connect_internet_button) #Connect Button
            if cbutton_state == 0:
                print("User pressed the connect button")
                enable_AP() #launch access point and reboot
                time.sleep(1)

            abutton_state = get_button_state(action_button) #Water Button
            if abutton_state == 0:
                if cs.feature_toggles["action_button"] == "1":
                    if cs.feature_toggles["action_water"] == "1":
                        run_water(60)
                if cs.feature_toggles["action_camera"] == "1":
                        camera_element.actuate(0)

            if time.time() - led_timer > 5: #send data to LED every 5s
                update_LED()
                led_timer = time.time()

    except(KeyboardInterrupt):
        GPIO.cleanup()

if __name__ == '__main__':
    led_timer, connect_timer = main_setup()
    main_loop(led_timer, connect_timer)
    