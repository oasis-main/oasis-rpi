#This is the program root, main.py. Run this file from the command line, in cron, through systemd, or in rc.local

#import shell modules
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')

#time
import time
import datetime

#concurrency
import rusty_pipes
from utils import concurrent_state as cs

#connectivity
from networking import db_tools as dbt
from networking import firebase_manager
from networking import wifi

#hardware
import rusty_pins
from utils import physics
from peripherals import buttons
from peripherals import relays
from peripherals import microcontroller_manager as minion

#housekeeping
from utils import reset_model
from utils import error_handler as err

#declare subprocess management variables
core = None
led = None
listener = None

#checks in the the core process has been called from the command line, or explicitly deactivated
def cmd_line_args():
    try:
        if sys.argv[1] == "run":
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1", db_writer = dbt.patch_firebase)
            print("Command line set core to run. Launching device engine...")
        if sys.argv[1] == "idle":
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0", db_writer = dbt.patch_firebase)
            print("Command line set core to idle. Device engine is on standby.")
    except Exception as e: #if no arguments are given, the above will fail
        print("No command line arguments were given.")
        print("Defaulting to last saved mode or default if new.")

#checks whether system is booting in Access Point Mode, launches connection script if so
def launch_access_point(): 
    global minion

    #launch server subprocess to accept credentials over Oasis wifi network, does not wait
    server_process = rusty_pipes.Open(["sudo", "streamlit", "run", "/home/pi/oasis-grow/networking/connect_oasis.py", "--server.headless=true", "--server.port=80", "--server.address=192.168.4.1", "--server.enableCORS=false", "--server.enableWebsocketCompression=false"],"access_point")
    print("Access Point Mode enabled")

    time.sleep(3)

    buttons.setup_button_interface(cs.structs["hardware_config"])

    if minion.ser_out is not None:
        #set led_status = "connectWifi"
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","accepting_wifi_connection", db_writer = dbt.patch_firebase)
        cs.load_state()
        #write LED state to seriaL
        while True: #place the "exit button" here to leave connection mode
            minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), "utf-8"))
            cbutton_state = buttons.get_button_state(buttons.connect_internet_button)
            if cbutton_state == 0:
                cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_idle", db_writer = dbt.patch_firebase)
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), "utf-8"))
                server_process.terminate("/home/pi/oasis-grow/configs/signals.json")
                wifi.enable_wifi()
                time.sleep(1)
    else:
        while True:
            cbutton_state = buttons.get_button_state(buttons.connect_internet_button)
            if cbutton_state == 0:
                server_process.terminate("/home/pi/oasis-grow/configs/signals.json")
                wifi.enable_wifi()
                time.sleep(1)

def connect_firebase():
    connect_firebase = rusty_pipes.Open(["python3", "/home/pi/oasis-grow/networking/firebase_manager.py"],"firebase_manager")

def start_listener():
    global listener
    if listener is None:
        listener = rusty_pipes.Open(["python3", "/home/pi/oasis-grow/networking/firebase_listener.py"],"listener")

def stop_listener():
    global listener
    if listener is not None:
        listener.terminate()
        listener.wait()
        listener = None

def start_core():
    global core
    cs.load_state()
    cs.load_locks()
    
    if (cs.locks["core_y"] == 0) & (core is None): #if it is free
        #launch it
        core = rusty_pipes.Open(["python3", "/home/pi/oasis-grow/core/core.py"],"core")
        print("Core process is running...")

        if cs.structs["device_state"]["connected"] == "1": #if connected
            #send LEDmode = "connected_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","connected_running", db_writer = dbt.patch_firebase)
        else: #if not connected
            #send LEDmode = "offline_running"
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","led_status","offline_running", db_writer = dbt.patch_firebase)

def stop_core():
    global core
    cs.load_state()
    cs.load_locks()
    
    if (cs.locks["core_y"] == 1) & (core is not None): #if it is running
        #kill it
        core.terminate()
        core.wait()
        core = None

        print("Core process is idle...")
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

def start_onboard_led():
    global led
    led = rusty_pipes.Open(["sudo", "python3", "/home/pi/oasis-grow/peripherals/neopixel_leds.py"],"led")

def stop_onboard_led():
    global led
    cs.load_state()
    cs.load_locks()

    if (cs.locks["led_y"] == 1) & (led is not None):
        led.terminate("/home/pi/oasis-grow/configs/signals.json")
        led.wait()
        led = None

#updates the state of the LED, serial must be set up,
def update_minion_led(): #Depends on: cs.load_state(), 'datetime'; Modifies: ser_out
    global minion
    cs.load_state()

    #write "off" or write status depending on ToD + settings
    now = datetime.datetime.now()
    HoD = now.hour

    if minion.ser_out is not None:
        if int(cs.structs["hardware_config"]["led_settings"]["time_start_led"]) < int(cs.structs["hardware_config"]["led_settings"]["time_stop_led"]):
            if HoD >= int(cs.structs["hardware_config"]["led_settings"]["time_start_led"]) and HoD < int(cs.structs["hardware_config"]["led_settings"]["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), 'utf-8')) #write status
                time.sleep(0.25)
                minion.ser_out.reset_output_buffer()
            if HoD < int(cs.structs["hardware_config"]["led_settings"]["time_start_led"]) or HoD >= int(cs.structs["hardware_config"]["led_settings"]["time_stop_led"]):
                minion.ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.structs["hardware_config"]["led_settings"]["time_start_led"]) > int(cs.structs["hardware_config"]["led_settings"]["time_stop_led"]):
            if HoD >=  int(cs.structs["hardware_config"]["led_settings"]["time_start_led"]) or HoD < int(cs.structs["hardware_config"]["led_settings"]["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), 'utf-8')) #write status
            if HoD < int(cs.structs["hardware_config"]["led_settings"]["time_start_led"]) and  HoD >= int(cs.structs["hardware_config"]["led_settings"]["time_stop_led"]):
                minion.ser_out.write(bytes(str("off"+"\n"), 'utf-8')) #write off
        if int(cs.structs["hardware_config"]["led_settings"]["time_start_led"]) == int(cs.structs["hardware_config"]["led_settings"]["time_stop_led"]):
                minion.ser_out.write(bytes(str(cs.structs["device_state"]["led_status"]+"\n"), 'utf-8')) #write status
    else:
        #print("no serial connection, cannot update LED view")
        pass

def update_power_tracking():
    cs.write_state("/home/pi/oasis-grow/configs/power_data.json","boards_kwh", physics.kwh(float(cs.structs["hardware_config"]["equipment_wattage"]["boards"]), 3600.00))
    dbt.patch_firebase_dict(cs.structs["access_config"], cs.structs["power_data"])
    
    if cs.structs["feature_toggles"]["save_power"] == "1": #should mimic how the core handles sensor data
        payload = cs.structs["power_data"]
        timestamp = {"time": str(datetime.datetime.now())} #add a timestamp
        payload.update(timestamp)
        firebase_manager.write_power_csv('/home/pi/oasis-grow/data_out/resource_use/power_data.csv')
        firebase_manager.send_csv('/home/pi/oasis-grow/data_out/resource_use/power_data.csv', "power_data.csv")

    reset_dict = {} #clear the power data over last hour, save to state
    for key in cs.structs["power_data"]:
        reset_dict.update({key: "0"})
    cs.write_dict("/home/pi/oasis-grow/configs/power_data.json",reset_dict)

#Executes update if connected & idle, waits for completion
def get_updates(): #depends on: cs.load_state(),'subproceess', update.py; modifies: system code, state variables
    print("Fetching over-the-air updates")
    cs.load_state()
    
    if cs.structs["device_state"]["running"] == "0": #replicated in the main loop
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase) #make sure the cloud does not update main code, kill listener
        dbt.kill_listener()
        #launch update.py and wait to complete
        update_process = rusty_pipes.Open(["python3", "/home/pi/oasis-grow/utils/update.py"],"update")
        update_process.wait()
        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1", db_writer = dbt.patch_firebase)#restore listener
    
    if cs.structs["device_state"]["running"] == "1": #replicated in the main loop
        #flip running to 0        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0", db_writer = dbt.patch_firebase)
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase) #make sure the cloud does not update main code, kill listener
        dbt.kill_listener()
        #launch update.py and wait to complete
        update_process = rusty_pipes.Open(["python3", "/home/pi/oasis-grow/utils/update.py"],"update")
        update_process.wait()
        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1", db_writer = dbt.patch_firebase) #restore running
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1", db_writer = dbt.patch_firebase)#restore listener

def export_timelapse():
    export_tl = rusty_pipes.Open(["python3", "/home/pi/oasis-grow/imaging/make_timelapse.py"])

def clear_data():
    reset_model.reset_data_out()
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "awaiting_clear_data_out", "0", db_writer = dbt.patch_firebase)

def main_setup():
    #Initialize Oasis-Grow:
    print("Initializing...")
    reset_model.reset_locks()
    cs.load_state() #get the device data
    
    if cs.structs["feature_toggles"]["onboard_led"] == "1":
        start_onboard_led()
    else:
        minion.start_serial_out() #start outbound serial command interface
    
    cs.check_state("access_point", launch_access_point) #check to see if the device should be in access point mode
                                                        #should block if so

    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = None) #set to 0 so listener launches
    connect_firebase() #listener will not be re-called unless a connection fails at some point

    cmd_line_args() #Check command line flags for special instructions

    buttons.setup_button_interface(cs.structs["hardware_config"]) #Setup on-device interface for interacting with device using buttons

    #start the clock for  refresh
    led_timer = time.time()
    connect_timer = time.time()
    power_timer = time.time()

    return led_timer, connect_timer, power_timer

def main_loop(led_timer, connect_timer, power_timer):
    try:
        while True:
            cs.load_state()

            if (time.time() - led_timer > 5) and (cs.structs["feature_toggles"]["onboard_led"] == "0"): #send data to LED every 5s
                update_minion_led()
                led_timer = time.time() #reset the timer

            if time.time() - connect_timer > 900: #check connection every 15 min (900s)
                connect_firebase()
                connect_timer = time.time()

            if time.time() - power_timer > 3600: #send last hour power data to firebase
                update_power_tracking()
                power_timer = time.time() #reset the timer
            
            cs.check_state("connected", start_listener, stop_listener) #if connected, listen to database
            cs.check_state("running", start_core, stop_core) #if running, start the sensors and controllers
            cs.check_state("awaiting_update", get_updates)
            cs.check_state("awaiting_deletion", firebase_manager.delete_device)
            cs.check_state("awaiting_clear_data_out", clear_data)
            cs.check_state("awaiting_timelapse", export_timelapse)

            sbutton_state = buttons.get_button_state(buttons.start_stop_button) #Start Button
            if sbutton_state == 0:
                print("User pressed the start/stop button")
                switch_core_running() #turn core on/off
                time.sleep(1)

            cbutton_state = buttons.get_button_state(buttons.connect_internet_button) #Connect Button
            if cbutton_state == 0:
                print("User pressed the connect button")
                if cs.structs["device_state"]["connected"] == "1":
                    wifi.enable_access_point(dbt.patch_firebase) #launch access point and reboot
                else:
                    wifi.enable_access_point()
                time.sleep(1)

            if cs.structs["feature_toggles"]["action_button"] == "1":
                abutton_state = buttons.get_button_state(buttons.action_button) #Water Button
                if abutton_state == 0:
                    if cs.structs["feature_toggles"]["action_water"] == "1":
                        cs.load_locks()
                        if cs.locks["water_pump_y"] == 0:
                            cs.rusty_pipes.lock(cs.lock_filepath, "water_pump")
                            water_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["water_relay"]) #bcm pin # pulls from config file
                            pin = rusty_pins.GpioOut(water_GPIO)
                            relays.actuate_interval_sleep(pin, duration = float(cs.structs["control_params"]["watering_duration"]), sleep = float(cs.structs["control_params"]["watering_interval"]), duration_units="seconds", sleep_units="days", wattage=cs.structs["hardware_config"]["equipment_wattage"]["water_pump"], log="water_pump_kwh")
                            pin = None
                            cs.rusty_pipes.unlock(cs.lock_filepath, "water_pump")
                    if cs.structs["feature_toggles"]["action_camera"] == "1":
                        say_cheese = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/imaging/camera.py', "0"],"snapshot")
                        say_cheese.wait()
            
            time.sleep(0.25)

    except(KeyboardInterrupt):
        print("   <----- Exiting program...")
        reset_model.reset_device_state() #This is for testing purposes, to keep behavior the same between debugs

    except Exception as e:
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "led_status", "error", db_writer = dbt.patch_firebase)
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "device_error", str(err.full_stack()), db_writer = dbt.patch_firebase)
        print(err.full_stack())
    
    finally:
        stop_core()
        stop_listener()
        stop_onboard_led()
        
if __name__ == '__main__':
    led_timer, connect_timer, power_timer = main_setup()
    main_loop(led_timer, connect_timer, power_timer)
