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
#sys.path.append('/usr/lib/python37.zip')
#sys.path.append('/usr/lib/python3.7')
#sys.path.append('/usr/lib/python3.7/lib-dynload')
#sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
#sys.path.append('/usr/local/lib/python3.7/dist-packages')
#sys.path.append('/usr/lib/python3/dist-packages')

#import package modules
import RPi.GPIO as GPIO
import serial
import subprocess
from subprocess import Popen, PIPE, STDOUT
import multiprocessing
import signal

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
from networking import db_tools as dbt
from networking import wifi

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
    cs.load_state() #get the device data
    start_serial() #start outbound serial command interface
    check_AP() #check to see if the device should be in access point mode
    
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #set to 0 so listener launches
    dbt.connect_firebase() #listener will not be re-called unless a connection fails at some point

    cmd_line_args() #Check command line flags for special instructions

    setup_core_process() #launch sensor, data collection, & feedback management

    setup_button_interface() #Setup on-device interface for interacting with device using buttons
    
    if cs.feature_toggles["action_button"] == "1":
        if cs.feature_toggles["action_water"] == "1":
            setup_water()

    #start the clock for  refresh
    led_timer = time.time()
    connect_timer = time.time()

    return led_timer, connect_timer

def main_loop(led_timer, connect_timer):
    
    try:
        while True:
            cs.load_state() #refresh the state variables

            if time.time() - connect_timer > 600: #check connection every 10 min (600s)
                dbt.connect_firebase

            check_core_running() #check if core is supposed to be running

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
    