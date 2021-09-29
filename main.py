#This is the program root, main.py. Run this file from the command line, in cron, or in rc.local(preferred).

#Tips:
# Use the -b when installing with 'source ./master_setup.sh" to setup the bootloader ie. 'source ./master_setup.sh -b'

#import shell modules
import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
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
import reset_model

#declare state variables
device_state = None #describes the current state of the system
grow_params = None #describes the grow configuration of the system
hardware_config = None #holds hardware I/O setting & pin #s
access_config = None #contains credentials for connecting to firebase
feature_toggles = None #tells the system which features are in use

#declare process management variables
listener = None
ser_out = None #object for writing to the microcontroller via serial
grow_ctrl_process = None #variable to launch & manage the grow controller
water_relay = None #holds GPIO object for running the watering aparatus

#declare UI variables
start_stop_button = None #holds GPIO object for starting and stopping grow_ctrl process
connect_internet_button = None #holds GPIO object for connecting device to internet
run_water_button = None #holds GPIO object for triggering the watering aparatus

def load_state(loop_limit=100000): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, feature_toggles, access_config, grow_params

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/configs/device_state.json") as d:
                device_state = json.load(d) #get device state

            for k,v in device_state.items(): 
                if device_state[k] is None:
                    print("Read NoneType in device_state")
                    reset_model.reset_device_state()
                    reset_model.reset_grow_params()
                    reset_model.reset_nonhw_configs()
                    reset_model.reset_data_out()
                    reset_model.reset_logs()
                    print("Device has been reset to default configuration") 
                else: 
                    pass    
                
            with open("/home/pi/oasis-grow/configs/grow_params.json") as g:
                grow_params = json.load(g) #get grow params

            for k,v in grow_params.items(): 
                if grow_params[k] is None:
                    print("Read NoneType in grow_params")
                    reset_model.reset_device_state()
                    reset_model.reset_grow_params()
                    reset_model.reset_nonhw_configs()
                    reset_model.reset_data_out()
                    reset_model.reset_logs()
                    print("Device has been reset to default configuration") 
                else: 
                    pass      
                
            with open("/home/pi/oasis-grow/configs/access_config.json") as a:
                access_config = json.load(a) #get access state
                
            with open ("/home/pi/oasis-grow/configs/feature_toggles.json") as f:
                feature_toggles = json.load(f) #get feature toggles
        
        except Exception as e:
            print("Error occured while main.py reading. Retrying...")

#modifies a firebase variable
def patch_firebase(field,value): #Depends on: load_state(),'requests','json'; Modifies: database['field'], state variables
    load_state()
    data = json.dumps({field: value})
    url = "https://oasis-1757f.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)

#save key values to .json
def write_state(path,field,value,loop_limit=100000): #Depends on: load_state(), patch_firebase, 'json'; Modifies: path
    load_state()

    #these will be loaded in by the listener, so best to make sure we represent the change in firebase too
    if device_state["connected"] == "1": #write state to cloud
        try:
            patch_firebase(field,value)
        except Exception as e:
            print(e)
            pass

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open(path, "r+") as x: # open the file.
                data = json.load(x) # can we load a valid json?

                if path == "/home/pi/oasis-grow/configs/device_state.json": #are we working in device_state?
                    if data["device_state_write_available"] == "1": #check is the file is available to be written
                        data["device_state_write_available"] = "0" #let system know resource is not available
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate() 

                        data[field] = value #write the desired value
                        data["device_state_write_available"] = "1" #let system know resource is available again 
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        break #break the loop when the write has been successful

                    else:
                        pass

                elif path == "/home/pi/oasis-grow/configs/grow_params.json": #are we working in grow_params?
                    if data["grow_params_write_available"] == "1":
                        data["grow_params_write_available"] = "0" #let system know writer is not available
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        data["grow_params_write_available"] = "1"
                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        break  #break the loop when the write has been successful

                else: #otherwise, attempt a normal write
                    data[field] = value #write the desired value
                    x.seek(0)
                    json.dump(data, x)
                    x.truncate()

                    break #break the loop when the write has been successful

        except Exception as e: #If any of the above fails:
            print("Tried to write while another write was occuring, retrying...")
            print(e)
            pass #continue the loop until write is successful or cieling is hit

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
    write_state("/home/pi/oasis-grow/configs/access_config.json","id_token",refresh_req.json()["id_token"])
    write_state("/home/pi/oasis-grow/configs/access_config.json","local_id",refresh_req.json()["user_id"])

    print("Obtained local credentials")

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
        write_state("/home/pi/oasis-grow/configs/access_config.json","refresh_token", refresh_token)

        #bring in the refresh token for use further down
        load_state()
        refresh_token = access_config["refresh_token"]
        print("Obtained refresh token")

        #fetch a new id_token & local_id
        get_local_credentials(refresh_token)

        #let firebase know the connection was successful
        patch_firebase("connected","1")

        #update the device state to "connected"
        write_state('/home/pi/oasis-grow/configs/device_state.json',"connected","1")
        print("Device is connected to the Oasis Network")

    except Exception as e:
        print(e) #display error
        #write state as not connected
        write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0")
        print("Could not connect to Oasis Network")

#check if the device is waiting to be added to firebase, if it is then add it, otherwise skip
def check_new_device(): #depends on: ;modifies:
    load_state()

    if device_state["new_device"] == "1":

        #assemble data to initialize firebase
        setup_dict = {}
        setup_dict.update(device_state)
        setup_dict.update(grow_params)
        setup_dict_named = {access_config["device_name"] : setup_dict}
        my_data = json.dumps(setup_dict_named)
        #print(my_data)
        #print(type(my_data))

        #add box data to firebase
        url = "https://oasis-1757f.firebaseio.com/"+access_config["local_id"]+".json?auth="+access_config["id_token"]
        post_request = requests.patch(url,my_data)
        #print(post_request.ok)
        if post_request.ok:
            write_state("/home/pi/oasis-grow/configs/device_state.json","new_device","0")
            print("New device added to firebase")
        else:
            print("Failed to add new device")

#checks for available updates, executes if connected & idle, waits for completion
def check_updates(): #depends on: load_state(),'subproceess', update.py; modifies: system code, state variables
    load_state()
    if device_state["running"] == "0" and device_state["awaiting_update"] == "1": #replicated in the main loop
        #kill listener
        write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        #launch update.py and wait to complete
        update_process = Popen(["sudo", "python3", "/home/pi/oasis-grow/utils/update.py"])
        write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
    if device_state["running"] == "1" and device_state["awaiting_update"] == "1": #replicated in the main loop
        #flip running to 0        
        write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")
        #kill listener
        write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        #launch update.py and wait to complete
        update_process = Popen(["sudo", "python3", "/home/pi/oasis-grow/utils/update.py"])
        write_state("/home/pi/oasis-grow/configs/device_state.json","running","1") #restore running
        write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener
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
    load_state()
    if device_state["deleted"] == "1" and listener is not None:
        print("Removing device from Oasis Network...")
        write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        print("Database monitoring deactivated")
        reset_model.reset_device_state()
        reset_model.reset_grow_params()
        reset_model.reset_nonhw_configs()
        #reset_model.reset_data_out()
        reset_model.reset_logs()
        print("Device has been reset to default configuration")
        systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])


#setup buttons for the main program interface
def setup_button_interface(): #depends on: load_state(), 'RPi.GPIO'; modifies: start_stop_button, connect_internet_button, run_water_button, state variables
    global start_stop_button, connect_internet_button, run_water_button
    #specify gpio pin number mode
    GPIO.setmode(GPIO.BCM)

    #get hardware configuration
    load_state()

    #set button pins
    start_stop_button = hardware_config["button_gpio_map"]["start_stop_button"]
    connect_internet_button = hardware_config["button_gpio_map"]["connect_internet_button"]
    run_water_button = hardware_config["button_gpio_map"]["run_water_button"]

    #Setup buttons
    GPIO.setup(start_stop_button, GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(connect_internet_button,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(run_water_button,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#setup restart button for Access Point Button
def setup_button_AP(): #Depends on: load_state(), 'RPi.GPIO'; Modifies: connect_internet_button, state variables
    global connect_internet_button
    GPIO.setmode(GPIO.BCM)

    #get hardware configuration
    load_state()

    #set button pins
    connect_internet_button = hardware_config["button_gpio_map"]["connect_internet_button"]

    #Setup buttons
    GPIO.setup(connect_internet_button,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#gets the state of a button (returns 1 if not pressed, 0 if pressed)
def get_button_state(button): #Depends on: RPi.GPIO; Modifies: None
    state = GPIO.input(button)
    return state

#reconfigures network interface, tells system to boot with Access Point, restarts
def enable_AP(): #Depends on: write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should be launched on next controller startup
    write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","1")

    #disable WiFi, enable AP, reboot
    config_ap_dhcpcd = Popen(["sudo", "cp", "/etc/dhcpcd_AP.conf", "/etc/dhcpcd.conf"])
    config_ap_dhcpcd.wait()
    config_ap_dns = Popen(["sudo", "cp", "/etc/dnsmasq_AP.conf", "/etc/dnsmasq.conf"])
    config_ap_dns.wait()
    enable_hostapd = Popen(["sudo", "systemctl", "enable", "hostapd"])
    enable_hostapd.wait()
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])

#reconfigures network interface, tells system to boot with WiF, restarts
def enable_WiFi(): #Depends on: write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should not be launched on next controller startup
    write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","0")

    #disable WiFi, enable AP, reboot
    config_wifi_dchpcd = Popen(["sudo", "cp", "/etc/dhcpcd_WiFi.conf", "/etc/dhcpcd.conf"])
    config_wifi_dchpcd.wait()
    config_wifi_dns = Popen(["sudo", "cp", "/etc/dnsmasq_WiFi.conf", "/etc/dnsmasq.conf"])
    config_wifi_dns.wait()
    disable_hostapd = Popen(["sudo", "systemctl", "disable hostapd"])
    disable_hostapd.wait()
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])

#checks whether system is booting in Access Point Mode, launches connection script if so
def check_AP(): #Depends on: 'subprocess', oasis_server.py, setup_button_AP(); Modifies: state_variables, 'ser_out', device_state.json
    global ser_out, connect_internet_button
    load_state()
    if device_state["access_point"] == "1":
        #launch server subprocess to accept credentials over Oasis wifi network, does not wait
        server_process = Popen(["sudo", "streamlit", "run", "/home/pi/oasis-grow/networking/oasis_setup.py", "--server.headless=true", "--server.port=80", "--server.address=192.168.4.1", "--server.enableCORS=false", "--server.enableWebsocketCompression=false"])
        print("Access Point Mode enabled")

        setup_button_AP()

        if ser_out is not None:
            #set led_status = "connectWifi"
            write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","accepting_wifi_connection")
            load_state()
            #write LED state to seriaL
            while True: #place the "exit button" here to leave connection mode
                ser_out.write(bytes(str(device_state["led_status"]+"\n"), "utf-8"))
                cbutton_state = get_button_state(connect_internet_button)
                if cbutton_state == 0:
                    write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle")
                    ser_out.write(bytes(str(device_state["led_status"]+"\n"), "utf-8"))
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

#check if grow_ctrl is supposed to be running, launch it if so. Do nothing if not
def setup_growctrl_process(): #Depends on: load_state(), write_state(), 'subprocess'; Modifies: grow_ctrl_process, state_variables, device_state.json
    global grow_ctrl_process
    load_state()

    #if the device is supposed to be running
    if device_state["running"] == "1":

        #launch grow_ctrl main
        grow_ctrl_process = Popen(["sudo", "python3", "/home/pi/oasis-grow/core/grow_ctrl.py", "main"])

        if device_state["connected"] == "1": #if connected
            #LEDmode = "connected_running"
            write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running")
        else: #if not connected
            write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running")

        print("launched grow controller")

    else:

        #launch sensing-feedback subprocess in daemon mode
        grow_ctrl_process = Popen(["sudo", "python3", "/home/pi/oasis-grow/core/grow_ctrl.py", "daemon"])

        if device_state["connected"] == "1": #if connected
            #LEDmode = "connected_idle"
            write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle")
        else: #if not connected
            write_state('/home/pi/oasis-grow/configs/device_state.json',"led_status","offline_idle")

        print("grow controller not launched")

#checks in the the core process has been called from the command line
def cmd_line_args():
    try:
        if sys.argv[1] == "run":
            write_state("/home/pi/oasis-grow/configs/device_state.json","running","1")
            print("Command line argument set to run")
        if sys.argv[1] == "idle":
            write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")
            print("Command line argument set to idle")
    except Exception as e:
        print("Defaulting to last saved mode...")

#checks if growctrl should be running, starts it if so, kills it otherwise
def check_growctrl_running(): #Depends on: load_state(), write_state(), 'subprocess'; Modifies: grow_ctrl_process, state variables, device_state.json
    global grow_ctrl_process
    load_state()

    #if the device is supposed to be running
    if device_state["running"] == "1":

        poll_grow_ctrl = grow_ctrl_process.poll() #check if grow_ctrl process is running
        if poll_grow_ctrl is not None: #if it is not running
            #launch it
            grow_ctrl_process = Popen(["sudo", "python3", "/home/pi/oasis-grow/core/grow_ctrl.py", "main"])
            print("launched grow-ctrl")

            if device_state["connected"] == "1": #if connected
                #send LEDmode = "connected_running"
                write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running")
            else: #if not connected
                #send LEDmode = "offline_running"
                write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running")

    else:

        poll_grow_ctrl = grow_ctrl_process.poll() #check if grow_ctrl process is running
        if poll_grow_ctrl is None: #if it is running
            try: #try to kill it
                grow_ctrl_process.terminate()
                grow_ctrl_process.wait()
                print("grow_ctrl_process deactivated")
            except:
                pass

            if device_state["connected"] == "1": #if connected
                #send LEDmode = "connected_idle"
                write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle")
            else: #if not connected
                #send LEDmode = "offline_idle"
                write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle")

#checks if growctrl is running, kills it if so, starts it otherwise
def switch_growctrl_running(): #Depends on: load_state(), write_state(), patch_firebase(), 'subprocess'; Modifies: device_state.json, state_variables
    load_state()

    #if the device is set to running
    if device_state["running"] == "1":
        #set running state to off = 0
        write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")

    #if not set to running
    else:
        #set running state to on = 1
        write_state("/home/pi/oasis-grow/configs/device_state.json","running","1")

#sets up the watering aparatus
def setup_water(): #Depends on: load_state(), 'RPi.GPIO'; Modifies: water_relay
    global water_relay
    #get hardware configuration
    load_state()

    #set watering GPIO
    water_relay = hardware_config["actuator_gpio_map"]["water_relay"] #watering aparatus
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
def update_LED(): #Depends on: load_state(), 'datetime'; Modifies: ser_out
    global ser_out
    load_state()

    #write "off" or write status depending on ToD + settings
    now = datetime.datetime.now()
    HoD = now.hour

    if ser_out is not None:
        if int(device_state["time_start_led"]) < int(device_state["time_stop_led"]):
            if HoD >= int(device_state["time_start_led"]) and HoD < int(device_state["time_stop_led"]):
                ser_out.write(bytes(str(device_state["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(device_state["time_start_led"]) or HoD >= int(device_state["time_stop_led"]):
                ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(device_state["time_start_led"]) > int(device_state["time_stop_led"]):
            if HoD >=  int(device_state["time_start_led"]) or HoD < int(device_state["time_stop_led"]):
                ser_out.write(bytes(str(device_state["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(device_state["time_start_led"]) and  HoD >= int(device_state["time_stop_led"]):
                ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(device_state["time_start_led"]) == int(device_state["time_stop_led"]):
                ser_out.write(bytes(str(device_state["led_status"]+"\n"), 'utf-8')) #write status
    else:
        #print("no serial connection, cannot update LED view")
        pass

if __name__ == '__main__':

    #Initialize Oasis:
    print("Initializing...")
    time.sleep(10)
    load_state()
    start_serial()
    check_AP()
    connect_firebase()

    load_state()
    if device_state["connected"] == "1":
        check_new_device()
        check_updates()
        check_deleted()
        launch_listener()

    #Check if command line set to run
    cmd_line_args()

    #launch core process
    setup_growctrl_process()

    #Setup on-device interface
    setup_button_interface()
    setup_water()

    #start the clock for timing credential refresh &  data exchanges with LED
    led_timer = time.time()
    token_timer = time.time()

    try:
        while True:
            load_state() #refresh the state variables

            check_growctrl_running() #check if growctrl is supposed to be running

            if device_state["connected"] == "1":
               check_updates() #check if the machine needs to be update
               check_deleted() #check if the user is trying to delete this device
               if time.time() - token_timer > 600: #refresh the local credentials every 10 min (600s)
                    token_timer = time.time()
                    get_local_credentials(access_config["refresh_token"])

            sbutton_state = get_button_state(start_stop_button) #Start Button
            if sbutton_state == 0:
                print("User pressed the start/stop button")
                switch_growctrl_running() #turn growctrl on/off
                time.sleep(1)

            cbutton_state = get_button_state(connect_internet_button) #Connect Button
            if cbutton_state == 0:
                print("User pressed the connect button")
                enable_AP() #launch access point and reboot
                time.sleep(1)

            wbutton_state = get_button_state(run_water_button) #Water Button
            if wbutton_state == 0:
                run_water(60) #run the water for 60 seconds
                time.sleep(1)

            if time.time() - led_timer > 5: #send data to LED every 5s
                update_LED()
                led_timer = time.time()

    except(KeyboardInterrupt):
        GPIO.cleanup()
