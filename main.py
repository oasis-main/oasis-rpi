#This is the program root, main.py. Run this file from the command line, in cron, through systemd, or in rc.local

#import shell modules
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')

#data
import json

#concurrency
from subprocess import Popen
import multiprocessing

#time
import time
import datetime

#other oasis-raspi packages
from utils import concurrent_state as cs
from utils import reset_model
from utils import error_handler as err
from networking import db_tools as dbt
from networking import wifi
from peripherals import buttons as btn
from peripherals import microcontroller_manager as minion

from equipment import water_pump

#declare process management variables
core_process = None #variable to launch & manage the grow controller

#checks whether system is booting in Access Point Mode, launches connection script if so
def launch_AP(): #Depends on: 'subprocess', oasis_server.py, setup_button_AP(); Modifies: state_variables, 'ser_out', device_state.json
    global minion, connect_internet_button

    #launch server subprocess to accept credentials over Oasis wifi network, does not wait
    server_process = Popen(["sudo", "streamlit", "run", "/home/pi/oasis-grow/networking/connect_oasis.py", "--server.headless=true", "--server.port=80", "--server.address=192.168.4.1", "--server.enableCORS=false", "--server.enableWebsocketCompression=false"])
    print("Access Point Mode enabled")

    time.sleep(3)

    btn.setup_button_interface()

    if minion.ser_out is not None:
        #set led_status = "connectWifi"
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","accepting_wifi_connection", db_writer = dbt.patch_firebase)
        cs.load_state()
        #write LED state to seriaL
        while True: #place the "exit button" here to leave connection mode
            minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), "utf-8"))
            cbutton_state = btn.get_button_state(btn.connect_internet_button)
            if cbutton_state == 0:
                cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle", db_writer = dbt.patch_firebase)
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), "utf-8"))
                server_process.terminate()
                wifi.enable_WiFi()
                time.sleep(1)
    else:
        while True:
            cbutton_state = btn.get_button_state(btn.connect_internet_button)
            if cbutton_state == 0:
                server_process.terminate()
                wifi.enable_WiFi()
                time.sleep(1)

#check if core is supposed to be running, launch it if so. Do nothing if not
def setup_core_process(): #Depends on: cs.load_state(), cs.write_state(), 'subprocess'; Modifies: core_process, state_variables, device_state.json
    global core_process
    cs.load_state()

    #if the device is supposed to be running
    if cs.structs["device_state"]["running"] == "1":

        #launch core main
        core_process = Popen(["python3", "/home/pi/oasis-grow/core/core.py", "main"])

        if cs.structs["device_state"]["connected"] == "1": #if connected
            #LEDmode = "connected_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running", db_writer = dbt.patch_firebase)
        else: #if not connected
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running", db_writer = dbt.patch_firebase)

        print("launched core process")

    else:

        #launch sensing-feedback subprocess in daemon mode
        core_process = Popen(["python3", "/home/pi/oasis-grow/core/core.py", "daemon"])

        if cs.structs["device_state"]["connected"] == "1": #if connected
            #LEDmode = "connected_idle"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle", db_writer = dbt.patch_firebase)
        else: #if not connected
            cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"led_status","offline_idle", db_writer = dbt.patch_firebase)

        print("core process not launched")

#checks in the the core process has been called from the command line
def cmd_line_args():
    try:
        if sys.argv[1] == "run":
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1", db_writer = dbt.patch_firebase)
            print("Command line argument set to run")
        if sys.argv[1] == "idle":
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0", db_writer = dbt.patch_firebase)
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

        if cs.structs["device_state"]["connected"] == "1": #if connected
            #send LEDmode = "connected_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running", db_writer = dbt.patch_firebase)
        else: #if not connected
            #send LEDmode = "offline_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running", db_writer = dbt.patch_firebase)

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

        if cs.structs["device_state"]["connected"] == "1": #if connected
            #send LEDmode = "connected_idle"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_idle", db_writer = dbt.patch_firebase)
        else: #if not connected
            #send LEDmode = "offline_idle"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle", db_writer = dbt.patch_firebase)

#checks if core is running, kills it if so, starts it otherwise
def switch_core_running(): #Depends on: cs.load_state(), cs.write_state(), dbt.patch_firebase(), 'subprocess'; Modifies: device_state.json, state_variables
    cs.load_state()

    #if the device is set to running
    if cs.structs["device_state"]["running"] == "1":
        #set running state to off = 0
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0",db_writer = dbt.patch_firebase)

    #if not set to running
    else:
        #set running state to on = 1
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1", db_writer = dbt.patch_firebase)

#Executes update if connected & idle, waits for completion
def get_updates(): #depends on: cs.load_state(),'subproceess', update.py; modifies: system code, state variables
    print("Fetching over-the-air updates")
    cs.load_state()
    
    if cs.structs["device_state"]["running"] == "0": #replicated in the main loop
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase) #make sure the cloud does not update main code, kill listener
        dbt.kill_listener()
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1", db_writer = dbt.patch_firebase)#restore listener
    
    if cs.structs["device_state"]["running"] == "1": #replicated in the main loop
        #flip running to 0        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0", db_writer = dbt.patch_firebase)
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase) #make sure the cloud does not update main code, kill listener
        dbt.kill_listener()
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1", db_writer = dbt.patch_firebase) #restore running
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1", db_writer = dbt.patch_firebase)#restore listener

#deletes a box if the cloud is indicating that it should do so
def delete_device():    
    print("Removing device from Oasis Network...")
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase) #make sure it doesn't write anything to the cloud

    print("Database monitoring deactivated")
    reset_model.reset_nonhw_configs()
    
    print("Device has been reset to default configuration")
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])
    systemctl_reboot.wait()

#check if the device is waiting to be added to firebase, if it is then add it, otherwise skip
def add_new_device():
    cs.load_state()

    #assemble data to initialize firebase
    setup_dict = {} #Access & hardware config will be kept private, not shared with cloud 
    setup_dict.update(cs.structs["device_state"])
    setup_dict.update(cs.structs["device_params"])
    setup_dict.update(cs.structs["feature_toggles"])
    setup_dict.update(cs.structs["sensor_info"])
    setup_dict_named = {cs.structs["access_config"]["device_name"] : setup_dict}
    my_data = setup_dict_named
    #print(my_data)
    #print(type(my_data))

    #add box data to firebase (replace with send_dict)
    patch_request = dbt.firebase_add_device(cs.structs["access_config"],my_data)
    
    if patch_request.ok:
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","new_device","0", db_writer = dbt.patch_firebase)
        print("New device added to firebase")
    else:
        print("Failed to add new device")

#connects system to firebase
def connect_firebase(): #depends on: cs.load_state(), cs.write_state(), dbt.patch_firebase(), 'requests'; Modifies: access_config.json, device_state.json
    
    #load state so we can use access credentials
    cs.load_state()
    wak = cs.structs["access_config"]["wak"]
    email = cs.structs["access_config"]["e"]
    password = cs.structs["access_config"]["p"]

    print("Checking for connection...")

    def try_connect():
        try:
            print("FireBase verification...")

            #fetch refresh token
            refresh_token = dbt.get_refresh_token(wak, email, password)

            #fetch refresh token and save to access_config
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","refresh_token", refresh_token, db_writer = None)

            #bring in the refresh token for use further down
            cs.load_state()
            refresh_token = cs.structs["access_config"]["refresh_token"]
            print("Obtained refresh token")

            #fetch a new id_token & local_id
            id_token, user_id = dbt.get_local_credentials(wak, refresh_token)

            #write local credentials to access config
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","id_token", id_token, db_writer = None)
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","local_id", user_id, db_writer = None)
            print("Obtained local credentials")

            #launch new_device check at network startup
            cs.check_state("new_device", add_new_device)

            #start listener to bring in db changes on startup
            #Main setup always sets local var to "0"
            dbt.launch_listener() #Flip local + cloud connected to 1 and start listener
            cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"connected","1", db_writer = dbt.patch_firebase)
        
            #update the device state to "connected"
            print("Device is connected over HTTPS to the Oasis Network")
            
        except Exception as e:
            print(err.full_stack()) #display error
            #write state as not connected
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase)
            print("Could not establish an HTTPS connection to Oasis Network")

    connection_attempt = multiprocessing.Process(target = try_connect)
    connection_attempt.start()

#updates the state of the LED, serial must be set up,
def update_minion_led(): #Depends on: cs.load_state(), 'datetime'; Modifies: ser_out
    global minion
    cs.load_state()

    #write "off" or write status depending on ToD + settings
    now = datetime.datetime.now()
    HoD = now.hour

    if minion.ser_out is not None:
        if int(cs.structs["device_params"]["time_start_led"]) < int(cs.structs["device_params"]["time_stop_led"]):
            if HoD >= int(cs.structs["device_params"]["time_start_led"]) and HoD < int(cs.structs["device_params"]["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(cs.structs["device_params"]["time_start_led"]) or HoD >= int(cs.structs["device_params"]["time_stop_led"]):
                minion.ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.structs["device_params"]["time_start_led"]) > int(cs.structs["device_params"]["time_stop_led"]):
            if HoD >=  int(cs.structs["device_params"]["time_start_led"]) or HoD < int(cs.structs["device_params"]["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(cs.structs["device_params"]["time_start_led"]) and  HoD >= int(cs.structs["device_params"]["time_stop_led"]):
                minion.ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.structs["device_params"]["time_start_led"]) == int(cs.structs["device_params"]["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), 'utf-8')) #write status
    else:
        #print("no serial connection, cannot update LED view")
        pass

def export_timelapse():
    export_tl = Popen(["python3", "/home/pi/oasis-grow/imaging/make_timelapse.py"])

def clear_data():
    reset_model.reset_data_out()
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "awaiting_clear_data_out", "0", db_writer = dbt.patch_firebase)

def launch_onboard_led():
    launch_led = Popen(["sudo", "python3", "/home/pi/oasis-grow/peripherals/neopixel_leds.py"])

def main_setup():
    #Initialize Oasis-Grow:
    print("Initializing...")
    reset_model.reset_locks()
    cs.load_state() #get the device data
    
    if cs.structs["feature_toggles"]["onboard_led"] == "1":
        launch_onboard_led()
    else:
        minion.start_serial_out() #start outbound serial command interface
    
    cs.check_state("access_point", launch_AP) #check to see if the device should be in access point mode
    
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = None) #set to 0 so listener launches
    connect_firebase() #listener will not be re-called unless a connection fails at some point

    cmd_line_args() #Check command line flags for special instructions
    
    setup_core_process() #launch sensor, data collection, & feedback management

    btn.setup_button_interface() #Setup on-device interface for interacting with device using buttons

    #start the clock for  refresh
    led_timer = time.time()
    connect_timer = time.time()

    return led_timer, connect_timer

def main_loop(led_timer, connect_timer):
    
    try:
        while True:
            cs.load_state()

            if cs.structs["feature_toggles"]["onboard_led"] == "0":
                update_minion_led()

            if time.time() - connect_timer > 900: #check connection every 15 min (900s)
                connect_firebase()
                connect_timer = time.time()
            
            cs.check_state("awaiting_update", get_updates)
            cs.check_state("awaiting_deletion", delete_device)
            cs.check_state("awaiting_clear_data_out", clear_data)
            cs.check_state("awaiting_timelapse", export_timelapse)

            cs.check_state("running", start_core, stop_core) #check if core is supposed to be running

            sbutton_state = btn.get_button_state(btn.start_stop_button) #Start Button
            if sbutton_state == 0:
                print("User pressed the start/stop button")
                switch_core_running() #turn core on/off
                time.sleep(1)

            cbutton_state = btn.get_button_state(btn.connect_internet_button) #Connect Button
            if cbutton_state == 0:
                print("User pressed the connect button")
                if cs.structs["device_state"]["connected"] == "1":
                    wifi.enable_AP(dbt.patch_firebase) #launch access point and reboot
                else:
                    wifi.enable_AP()
                time.sleep(1)

            if cs.structs["feature_toggles"]["action_button"] == "1":
                abutton_state = btn.get_button_state(btn.action_button) #Water Button
                if abutton_state == 0:
                    if cs.structs["feature_toggles"]["action_water"] == "1":
                        water_pump.actuate(60, )
                    if cs.structs["feature_toggles"]["action_camera"] == "1":
                        say_cheese = Popen(['python3', '/home/pi/oasis-grow/imaging/camera.py', "0"])
                        say_cheese.wait()
            if time.time() - led_timer > 5: #send data to LED every 5s
                update_minion_led()
                led_timer = time.time()

    except(KeyboardInterrupt):
        time.sleep(5)
        reset_model.reset_device_state()

    except Exception as e:
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "led_status", "error", db_writer = dbt.patch_firebase)
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "device_error", str(err.full_stack()), db_writer = dbt.patch_firebase)
        print(err.full_stack())
        
if __name__ == '__main__':
    led_timer, connect_timer = main_setup()
    main_loop(led_timer, connect_timer)
