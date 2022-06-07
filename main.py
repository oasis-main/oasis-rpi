#This is the program root, main.py. Run this file from the command line, in cron, through systemd, or in rc.local

#import shell modules
import sys
import os

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')

#data
import json

#peripherals
import RPi.GPIO as GPIO

#concurrency
from subprocess import Popen, PIPE, STDOUT
import multiprocessing

#time
import time
import datetime

#other oasis packages
from utils import concurrent_state as cs
from utils import reset_model
from utils import error_handler as err
from imaging import camera
from networking import db_tools as dbt
from networking import wifi
from minions import microcontroller_manager as minion
from peripherals import neopixel_leds as leds

#declare process management variables
core_process = None #variable to launch & manage the grow controller

#declare UI variables
start_stop_button = None #holds GPIO object for starting and stopping core process
connect_internet_button = None #holds GPIO object for connecting device to internet
action_button = None #holds GPIO object for triggering the desired action

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

#gets the state of a button (returns 1 if not pressed, 0 if pressed)
def get_button_state(button): #Depends on: RPi.GPIO; Modifies: None
    state = GPIO.input(button)
    return state

#checks whether system is booting in Access Point Mode, launches connection script if so
def launch_AP(): #Depends on: 'subprocess', oasis_server.py, setup_button_AP(); Modifies: state_variables, 'ser_out', device_state.json
    global minion, connect_internet_button

    #launch server subprocess to accept credentials over Oasis wifi network, does not wait
    server_process = Popen(["sudo", "streamlit", "run", "/home/pi/oasis-grow/networking/connect_oasis.py", "--server.headless=true", "--server.port=80", "--server.address=192.168.4.1", "--server.enableCORS=false", "--server.enableWebsocketCompression=false"])
    print("Access Point Mode enabled")

    setup_button_interface()

    if minion.ser_out is not None:
        #set led_status = "connectWifi"
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","accepting_wifi_connection")
        cs.load_state()
        #write LED state to seriaL
        while True: #place the "exit button" here to leave connection mode
            minion.ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), "utf-8"))
            cbutton_state = get_button_state(connect_internet_button)
            if cbutton_state == 0:
                cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle")
                minion.ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), "utf-8"))
                server_process.terminate()
                server_process.wait()
                wifi.enable_WiFi()
                time.sleep(1)
    else:
        while True:
            cbutton_state = get_button_state(connect_internet_button)
            if cbutton_state == 0:
                server_process.terminate()
                server_process.wait()
                wifi.enable_WiFi()
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

        print("launched core process")

    else:

        #launch sensing-feedback subprocess in daemon mode
        core_process = Popen(["python3", "/home/pi/oasis-grow/core/core.py", "daemon"])

        if cs.device_state["connected"] == "1": #if connected
            #LEDmode = "connected_idle"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle")
        else: #if not connected
            cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"led_status","offline_idle")

        print("core process not launched")

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


def start_core():
    global core_process
    cs.load_state()
    poll_core = core_process.poll() #check if core process is running
    if poll_core is not None: #if it is not running
        #launch it
        core_process = Popen(["python3", "/home/pi/oasis-grow/core/core.py", "main"])
        print("launched core process")

        if cs.device_state["connected"] == "1": #if connected
            #send LEDmode = "connected_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running")
        else: #if not connected
            #send LEDmode = "offline_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running")

def stop_core():
    global core_process
    cs.load_state()
    poll_core = core_process.poll() #check if core process is running
    if poll_core is None: #if it is running
        try: #try to kill it
            core_process.terminate()
            core_process.wait()
            print("core process deactivated")
        except:
            pass

        if cs.device_state["connected"] == "1": #if connected
            #send LEDmode = "connected_idle"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle")
        else: #if not connected
            #send LEDmode = "offline_idle"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle")

#checks if core is running, kills it if so, starts it otherwise
def switch_core_running(): #Depends on: cs.load_state(), cs.write_state(), dbt.patch_firebase(), 'subprocess'; Modifies: device_state.json, state_variables
    cs.load_state()

    #if the device is set to running
    if cs.device_state["running"] == "1":
        #set running state to off = 0
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")

    #if not set to running
    else:
        #set running state to on = 1
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1")

#Executes update if connected & idle, waits for completion
def get_updates(): #depends on: cs.load_state(),'subproceess', update.py; modifies: system code, state variables
    cs.load_state()
    
    if cs.device_state["running"] == "0": #replicated in the main loop
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure the cloud does not update main code, kill listener
        dbt.kill_listener()
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener
    
    if cs.device_state["running"] == "1": #replicated in the main loop
        #flip running to 0        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure the cloud does not update main code, kill listener
        dbt.kill_listener()
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1") #restore running
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener

#deletes a box if the cloud is indicating that it should do so
def delete_device():    
    print("Removing device from Oasis Network...")
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud

    print("Database monitoring deactivated")
    reset_model.reset_nonhw_configs()
    
    print("Device has been reset to default configuration")
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])
    systemctl_reboot.wait()

#check if the device is waiting to be added to firebase, if it is then add it, otherwise skip
def add_new_device(): #depends on: modifies:
    cs.load_state()

    #assemble data to initialize firebase
    setup_dict = {} #Access & hardware config will be kept private, not shared with cloud 
    setup_dict.update(cs.device_state)
    setup_dict.update(cs.device_params)
    setup_dict.update(cs.feature_toggles)
    setup_dict.update(cs.sensor_info)
    setup_dict_named = {cs.access_config["device_name"] : setup_dict}
    my_data = json.dumps(setup_dict_named)
    #print(my_data)
    #print(type(my_data))

    #add box data to firebase (replace with send_dict)
    patch_request = dbt.patch_firebase_dict(cs.access_config,my_data)
    
    if patch_request.ok:
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","new_device","0")
        print("New device added to firebase")
    else:
        print("Failed to add new device")

#connects system to firebase
def connect_firebase(): #depends on: cs.load_state(), cs.write_state(), dbt.patch_firebase(), 'requests'; Modifies: access_config.json, device_state.json
    
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
            refresh_token = dbt.get_refresh_token(wak, email, password)

            #fetch refresh token and save to access_config
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","refresh_token", refresh_token)

            #bring in the refresh token for use further down
            cs.load_state()
            refresh_token = cs.access_config["refresh_token"]
            print("Obtained refresh token")

            #fetch a new id_token & local_id
            id_token, user_id = dbt.get_local_credentials(wak, refresh_token)

            #write local credentials to access config
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","id_token", id_token)
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","local_id", user_id)
            print("Obtained local credentials")

            #launch new_device check at network startup
            cs.check("new_device", add_new_device)

            #start listener to bring in db changes on startup
            if cs.device_state["connected"] == "0":
                dbt.patch_firebase(cs.access_config, "connected", "1")
                cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"connected","1", offline_only=True)
                dbt.launch_listener()
            else:
                cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"connected","1", offline_only= True)
            
            #update the device state to "connected"
            print("Device is connected over HTTPS to the Oasis Network")

            cs.load_state()
            
        except Exception as e:
            print(e) #display error
            #write state as not connected
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0")
            print("Could not establish an HTTPS connection to Oasis Network")

    connection_attempt = multiprocessing.Process(target = try_connect)
    connection_attempt.start()

#runs the watering aparatus for a supplied interval
def run_water(interval): #Depends on: 'RPi.GPIO'; Modifies: water_relay
    #get hardware configuration
    cs.load_state()

    #set watering GPIO
    water_relay = cs.hardware_config["equipment_gpio_map"]["water_relay"] #watering aparatus
    GPIO.setwarnings(False)
    GPIO.setup(water_relay, GPIO.OUT) #GPIO setup
    
    #turn on the pump
    GPIO.output(water_relay, GPIO.HIGH)
    #wait 60 seconds
    time.sleep(interval)
    #turn off the pump
    GPIO.output(water_relay, GPIO.LOW)

#updates the state of the LED, serial must be set up,
def update_LED(): #Depends on: cs.load_state(), 'datetime'; Modifies: ser_out
    global minion
    cs.load_state()

    #write "off" or write status depending on ToD + settings
    now = datetime.datetime.now()
    HoD = now.hour

    if minion.ser_out is not None:
        if int(cs.device_params["time_start_led"]) < int(cs.device_params["time_stop_led"]):
            if HoD >= int(cs.device_params["time_start_led"]) and HoD < int(cs.device_params["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(cs.device_params["time_start_led"]) or HoD >= int(cs.device_params["time_stop_led"]):
                minion.ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.device_params["time_start_led"]) > int(cs.device_params["time_stop_led"]):
            if HoD >=  int(cs.device_params["time_start_led"]) or HoD < int(cs.device_params["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(cs.device_params["time_start_led"]) and  HoD >= int(cs.device_params["time_stop_led"]):
                minion.ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.device_params["time_start_led"]) == int(cs.device_params["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.device_state["led_status"]+"\n"), 'utf-8')) #write status
    else:
        #print("no serial connection, cannot update LED view")
        pass

def export_timelapse():
    export_tl = Popen(["python3", "/home/pi/oasis-grow/imaging/make_timelapse.py"])

def main_setup():
    #Initialize Oasis-Grow:
    print("Initializing...")
    cs.load_state() #get the device data
    
    minion.start_serial_out() #start outbound serial command interface
    cs.check("access_point", launch_AP) #check to see if the device should be in access point mode
    
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #set to 0 so listener launches
    connect_firebase() #listener will not be re-called unless a connection fails at some point

    cmd_line_args() #Check command line flags for special instructions
    
    setup_core_process() #launch sensor, data collection, & feedback management

    setup_button_interface() #Setup on-device interface for interacting with device using buttons

    #start the clock for  refresh
    led_timer = time.time()
    connect_timer = time.time()

    return led_timer, connect_timer

def main_loop(led_timer, connect_timer):
    
    try:
        while True:
            cs.load_state() #refresh the state variables

            if cs.feature_toggles["onboard_led"] == "1":
                leds.run()

            if time.time() - connect_timer > 600: #check connection every 10 min (600s)
                dbt.connect_firebase
            
            cs.check("awaiting_update", get_updates)
            cs.check("awaiting_deletion", delete_device)
            cs.check("awaiting_clear_data_out", reset_model.reset_data_out)
            cs.check("awaiting_timelapse", export_timelapse)

            cs.check("running", start_core, stop_core) #check if core is supposed to be running

            sbutton_state = get_button_state(start_stop_button) #Start Button
            if sbutton_state == 0:
                print("User pressed the start/stop button")
                switch_core_running() #turn core on/off
                time.sleep(1)

            cbutton_state = get_button_state(connect_internet_button) #Connect Button
            if cbutton_state == 0:
                print("User pressed the connect button")
                wifi.enable_AP() #launch access point and reboot
                time.sleep(1)

            if cs.feature_toggles["action_button"] == "1":
                abutton_state = get_button_state(action_button) #Water Button
                if abutton_state == 0:
                    if cs.feature_toggles["action_water"] == "1":
                        run_water(60)
                    if cs.feature_toggles["action_camera"] == "1":
                        camera.actuate(0)

            if time.time() - led_timer > 5: #send data to LED every 5s
                update_LED()
                led_timer = time.time()

    except(KeyboardInterrupt):
        GPIO.cleanup()

    except Exception as e:
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "led_status", "error")
        print(err.full_stack())
        
if __name__ == '__main__':
    led_timer, connect_timer = main_setup()
    main_loop(led_timer, connect_timer)