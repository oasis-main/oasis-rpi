#---------------------------------------------------------------------------------------
#IMPORTS
#Shell, PID, Communication, Time
#---------------------------------------------------------------------------------------
#Setup Path
import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

#Process management
import serial
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal

#communicating with firebase
import requests

#data handling
import json
import csv
import pandas

#dealing with specific times of the day
import time
import datetime

#import oasis packages
import reset_model

#declare state variables
device_state = None #describes the current state of the system
access_config = None #contains credentials for connecting to firebase
feature_toggles = None #tells grow_ctrl which elements are active and which are not
grow_params = None #offers run parameters to oasis-grow

#declare process management variables
ser_in = None
sensor_info = None
heat_process = None
humidity_process = None
fan_process = None
light_process = None
camera_process = None
water_process = None

#declare sensor data variables
temperature = 0
humidity = 0
last_temperature = 0
last_humidity = 0
last_target_temperature = 0
last_target_humidity = 0
water_low = 0

#loads device state, hardware, and access configurations
def load_state(): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, feature_toggles, access_config, grow_params

    try:
        with open("/home/pi/device_state.json") as d:
            device_state = json.load(d) #get device state
    except ValueError:
        reset_model.reset_device_state()

    try:
        with open("/home/pi/access_config.json") as a:
            access_config = json.load(a) #get access state
    except ValueError:
        reset_model.reset_access_config()

    try:
        with open("/home/pi/grow_params.json") as g:
            grow_params = json.load(g)
    except ValueError:
        reset_model.reset_grow_params()

    try:
        with open ("/home/pi/feature_toggles.json") as f:
            feature_toggles = json.load(f)
    except ValueError:
        reset_model.reset_feature_toggles()

#save key values to .json
def write_state(path,field,value): #Depends on: load_state(), 'json'; Modifies: path
    load_state() #get connection status

    with open(path, "r+") as x: #write state to local files
        data = json.load(x)
        data[field] = value
        x.seek(0)
        json.dump(data, x)
        x.truncate()

#modifies a firebase variable
def patch_firebase(dict): #Depends on: load_state(),'requests','json'; Modifies: database{data}, state variables
    load_state()
    data = json.dumps(dict)
    url = "https://oasis-1757f.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)

#write some data to a .csv, takes a dictionary and a path
def write_csv(path, dict): #Depends on: 'pandas',
    #load dict into dataframe
    df = pandas.DataFrame(dict)
    #.csv write
    df.to_csv(str(path), sep='\t', header=None, mode='a')

#attempts connection to microcontroller
def start_serial(): #Depends on:'serial'; Modifies: ser_out
    global ser_in

    try:
        try:
            ser_in = serial.Serial("/dev/ttyUSB0", 9600)
            print("Started serial communication with Arduino Nano.")
        except:
            ser_in = serial.Serial("/dev/ttyACM0", 9600)
            print("Started serial communication with Arduino Uno.")
    except Exception as e:
        #ser_in = None
        print("Serial connection not found")

#gets data from serial THIS WILL HAVE TO BE DEPRECATED SOON IN FAVOR OF AN ON-BOARD SENSOR SUITE
def listen(): #Depends on 'serial', start_serial(); Modifies: ser_in, sensor_info, temperature, humidity, last_temperature, last_humidity, water_low
    #load in global vars
    global ser_in,sensor_info,temperature,humidity,last_temperature,last_humidity,water_low

    if ser_in == None:
        return

    #listen for data from aurdino
    sensor_info = ser_in.readline().decode('UTF-8').strip().split(' ')

    if len(sensor_info)<3:
        pass
    else:
        #print and save our data
        last_humidity = humidity
        humidity =float(sensor_info[0])

        last_temperature = temperature
        temperature =float(sensor_info[1])

        water_low = int(sensor_info[2])

#PD controller to modulate heater feedback
def heat_pd(temperature, target_temperature, last_temperature, last_target_temperature, P_heat, D_heat): #no dependencies
    err_temperature = target_temperature-temperature

    temperature_dot = temperature-last_temperature

    target_temperature_dot = target_temperature-last_target_temperature

    err_dot_temperature = target_temperature_dot-temperature_dot

    heat_level  = P_heat*err_temperature + D_heat*err_dot_temperature
    heat_level  = max(min(int(heat_level),100),0)

    return heat_level

#PD controller to modulate humidifier feedback
def hum_pd(humidity, target_humidity, last_humidity, last_target_humidity, P_hum, D_hum): #no dependencies
    err_humidity = target_humidity-humidity

    humidity_dot = humidity-last_humidity

    target_humidity_dot = target_humidity-last_target_humidity

    err_dot_humidity = target_humidity_dot-humidity_dot

    humidity_level  = P_hum*err_humidity + D_hum*err_dot_humidity
    humidity_level  = max(min(int(humidity_level),100),0)

    return humidity_level

#PD controller to modulate fan feedback
def fan_pd(temperature, humidity, target_temperature, target_humidity, last_temperature, last_humidity, last_target_temperature, last_target_humidity, Pt_fan, Ph_fan, Dt_fan, Dh_fan): #no dependencies
    err_temperature = temperature-target_temperature
    err_humidity = humidity-target_humidity

    temperature_dot = temperature-last_temperature
    humidity_dot = humidity-last_humidity

    target_temperature_dot = target_temperature-last_target_temperature
    target_humidity_dot = target_humidity-last_target_humidity

    err_dot_temperature = temperature_dot-target_temperature_dot
    err_dot_humidity = humidity_dot-target_humidity_dot

    fan_level  = Pt_fan*err_temperature + Ph_fan*err_humidity + Dt_fan*err_dot_temperature + Dh_fan*err_dot_humidity
    fan_level  = max(min(int(fan_level),100),0)

    return fan_level

#poll heat subprocess if applicable and relaunch/update actuators
def run_heat(intensity): #Depends on: 'subprocess'; Modifies: heat_process
    global heat_process

    try:
        poll_heat = heat_process.poll() #heat
        if poll_heat is not None:
            heat_process = Popen(['python3', '/home/pi/oasis-grow/heatingElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        heat_process = Popen(['python3', '/home/pi/oasis-grow//heatingElement.py', str(intensity)]) #If no process, then starts

#poll humidity subprocess if applicable and relaunch/update actuators
def run_hum(intensity): #Depends on: 'subprocess'; Modifies: hum_process
    global humidity_process

    try:
        poll_humidity = humidity_process.poll() #humidity
        if poll_humidity is not None:
            humidity_process = Popen(['python3', '/home/pi/oasis-grow//humidityElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        humidity_process = Popen(['python3', '/home/pi/oasis-grow//humidityElement.py', str(intensity)]) #If no process, then starts

#poll fan subprocess if applicable and relaunch/update actuators
def run_fan(intensity): #Depends on: 'subprocess'; Modifies: humidity_process
    global fan_process

    try:
        poll_fan = fan_process.poll() #fan
        if poll_fan is not None:
            fan_process = Popen(['python3', '/home/pi/oasis-grow/fanElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        fan_process = Popen(['python3', '/home/pi/oasis-grow//fanElement.py', str(intensity)]) #If no process, then starts

#poll light subprocess if applicable and relaunch/update actuators
def run_light(time_on, time_off, refresh_frequency):
    global light_process #Depends on: 'subprocess'; Modifies: light_process

    try:
        poll_light = light_process.poll() #light
        if poll_light is not None:
            light_process = Popen(['python3', '/home/pi/oasis-grow/lightingElement.py', str(time_on), str(time_off), str(refresh_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        light_process = Popen(['python3', '/home/pi/oasis-grow//lightingElement.py', str(time_on), str(time_off), str(refresh_frequency)]) #If no process, then starts

#poll camera subprocess if applicable and relaunch/update actuators
def run_camera(picture_frequency): #Depends on: 'subprocess'; Modifies: camera_process
    global camera_process

    try:
        poll_camera = camera_process.poll() #camera
        if poll_camera is not None:
            camera_process = Popen(['python3', '/home/pi/oasis-grow/cameraElement.py', str(picture_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        camera_process = Popen(['python3', '/home/pi/oasis-grow//cameraElement.py', str(picture_frequency)]) #If no process, then starts

#poll water subprocess if applicable and relaunch/update actuators
def run_water(watering_duration, watering_frequency): #Depends on: 'subprocess'; Modifies: water_process
    global water_process

    try:
        poll_water = water_process.poll() #water
        if poll_water is not None:
            water_process = Popen(['python3', '/home/pi/oasis-grow/wateringElement.py', str(watering_duration), str(watering_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        water_process = Popen(['python3', '/home/pi/oasis-grow//wateringElement.py', str(watering_duration), str(watering_frequency)]) #If no process, then starts

#terminates the program and all running subprocesses
def terminate_program(): #Depends on: load_state(), 'sys', 'subprocess' #Modifies: heat_process, humidity_process, fan_process, light_process, camera_process, water_process
    global heat_process, humidity_process, fan_process, light_process, camera_process, water_process

    print("Terminating Program...")

    load_state() #get feature toggles

    if (feature_toggles["heater"] == "1") and (heat_process != None): #go through toggles and kill active processes
        heat_process.terminate()
        heat_process.wait()

    if (feature_toggles["humidifier"] == "1") and (humidity_process != None):
        humidity_process.terminate()
        humidity_process.wait()

    if (feature_toggles["fan"] == "1") and (fan_process != None):
        fan_process.terminate()
        fan_process.wait()

    if (feature_toggles["light"] == "1") and (light_process != None):
        light_process.terminate()
        light_process.wait()

    if (feature_toggles["camera"] == "1") and (camera_process != None):
        camera_process.terminate()
        camera_process.wait()

    if (feature_toggles["water"] == "1") and (water_process != None):
        water_process.terminate()
        water_process.wait()

    #flip "running" to 1 to make usable from command line
    write_state("/home/pi/device_state.json", "running", "0")

    sys.exit()

if __name__ == '__main__':

    #Load state variables to start the main program
    load_state()

    #Exit early if opening subprocess daemon
    if str(sys.argv[1]) == "daemon":
        print("grow_ctrl daemon started")
        #log daemon start
        write_state('/home/pi/logs/growCtrl_log.json','last_start_mode',"daemon")
        #kill the program
        sys.exit()
    if str(sys.argv[1]) == "main":
        print("grow_ctrl main started")
        #log main start
        write_state('/home/pi/logs/growCtrl_log.json','last_start_mode',"main")
        #flip "running" to 1 to make usable from command line
        write_state("/home/pi/device_state.json", "running", "1")
        #continue with program execution
        pass
    else:
        print("please offer valid run parameters")
        sys.exit()

    #attempt to make serial connection
    start_serial()

    #start the clock for timimg .csv writes and data exchanges with server
    data_timer = time.time()
    sensor_log_timer = time.time()

    #launch main program loop
    try:
        print("------------------------------------------------------------")

        while True:

            last_target_temperature = int(grow_params["target_temperature"]) #save last temperature and humidity targets to calculate delta for PD controllers
            last_target_humidity = int(grow_params["target_humidity"])

            load_state() #regresh the state variables to get new parameters


            if (feature_toggles["temp_hum_sensor"] == "1") or (feature_toggles["water_low_sensor"] == "1"):
                try: #attempt to read data from sensor, raise exception if there is a problem
                    listen() #this will be changed to run many sensor functions as opposed to one serial listener
                except Exception as e:
                    print(e)
                    print("Serial Port Failure")

            if feature_toggles["heater"] == "1":
                print("Target Temperature: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(int(grow_params["target_temperature"]),temperature, heat_pd(temperature,
                                                                                                                                  int(grow_params["target_temperature"]),
                                                                                                                                  last_temperature,
                                                                                                                                  last_target_temperature,
                                                                                                                                  int(grow_params["P_temp"]),
                                                                                                                                  int(grow_params["D_temp"]))))
            if feature_toggles["humidifier"] == "1":
                print("Target Humidity: %.1f %% | Current: %.1f %% | Hum_PID: %s %%"%(int(grow_params["target_humidity"]), humidity, hum_pd(humidity,
                                                                                                                               int(grow_params["target_humidity"]),
                                                                                                                               last_humidity,
                                                                                                                               last_target_humidity,
                                                                                                                               int(grow_params["P_hum"]),
                                                                                                                               int(grow_params["D_hum"]))))

            if feature_toggles["fan"] == "1":
                print("Fan PD: %s %%"%(fan_pd(temperature,
                                              humidity,
                                              int(grow_params["target_temperature"]),
                                              int(grow_params["target_humidity"]),
                                              last_temperature,
                                              last_humidity,
                                              last_target_temperature,
                                              last_target_humidity,
                                              int(grow_params["Pt_fan"]),
                                              int(grow_params["Ph_fan"]),
                                              int(grow_params["Dt_fan"]),
                                              int(grow_params["Dh_fan"]))))

            if feature_toggles["light"] == "1":
                print("Light Turns on at: %i :00 Local Time  | Turns off at: %i :00 Local Time"%(int(grow_params["time_start_light"]), int(grow_params["time_start_dark"])))

            if feature_toggles["camera"] == "1":
                print("Image every %i minute(s)"%(int(grow_params["camera_interval"])))

            if feature_toggles["water"] == "1":
                print("Watering for: %i second(s) every: %i hour(s)"%(int(grow_params["watering_duration"]), int(grow_params["watering_interval"])))

            if feature_toggles["water_low_sensor"] == "1":
                if water_low == 1:
                    print("Water Level Low!")

            print("------------------------------------------------------------")

            #every hour, log past hour and shift 24 hours of sensor data
            if time.time() - sensor_log_timer > 3600:

                if feature_toggles["temp_hum_sensor"] == "1":
                    
                    #replace each log with the next most recent one
                    device_state["temperature_log"]["temp_2hour_ago"] = device_state["temperature_log"]["temp_1hour_ago"]
                    device_state["temperature_log"]["temp_3hour_ago"] = device_state["temperature_log"]["temp_2hour_ago"] 
                    device_state["temperature_log"]["temp_4hour_ago"] = device_state["temperature_log"]["temp_3hour_ago"] 
                    device_state["temperature_log"]["temp_5hour_ago"] = device_state["temperature_log"]["temp_4hour_ago"] 
                    device_state["temperature_log"]["temp_6hour_ago"] = device_state["temperature_log"]["temp_5hour_ago"]
                    device_state["temperature_log"]["temp_7hour_ago"] = device_state["temperature_log"]["temp_6hour_ago"]
                    device_state["temperature_log"]["temp_8hour_ago"] = device_state["temperature_log"]["temp_7hour_ago"] 
                    device_state["temperature_log"]["temp_9hour_ago"] = device_state["temperature_log"]["temp_8hour_ago"]
                    device_state["temperature_log"]["temp_10hour_ago"] = device_state["temperature_log"]["temp_9hour_ago"]
                    device_state["temperature_log"]["temp_11hour_ago"] = device_state["temperature_log"]["temp_10hour_ago"]
                    device_state["temperature_log"]["temp_12hour_ago"] = device_state["temperature_log"]["temp_11hour_ago"]
                    device_state["temperature_log"]["temp_13hour_ago"] = device_state["temperature_log"]["temp_12hour_ago"]
                    device_state["temperature_log"]["temp_14hour_ago"] = device_state["temperature_log"]["temp_13hour_ago"] 
                    device_state["temperature_log"]["temp_15hour_ago"] = device_state["temperature_log"]["temp_14hour_ago"]
                    device_state["temperature_log"]["temp_16hour_ago"] = device_state["temperature_log"]["temp_15hour_ago"]
                    device_state["temperature_log"]["temp_17hour_ago"] = device_state["temperature_log"]["temp_16hour_ago"]
                    device_state["temperature_log"]["temp_18hour_ago"] = device_state["temperature_log"]["temp_17hour_ago"]
                    device_state["temperature_log"]["temp_19hour_ago"] = device_state["temperature_log"]["temp_18hour_ago"]
                    device_state["temperature_log"]["temp_20hour_ago"] = device_state["temperature_log"]["temp_19hour_ago"]
                    device_state["temperature_log"]["temp_21hour_ago"] = device_state["temperature_log"]["temp_21hour_ago"]
                    device_state["temperature_log"]["temp_22hour_ago"] = device_state["temperature_log"]["temp_22hour_ago"]
                    device_state["temperature_log"]["temp_23hour_ago"] = device_state["temperature_log"]["temp_23hour_ago"]
                    device_state["temperature_log"]["temp_24hour_ago"] = device_state["temperature_log"]["temp_24hour_ago"]
                    
                    device_state["humidity_log"]["hum_2hour_ago"] = device_state["humidity_log"]["hum_1hour_ago"]
                    device_state["humidity_log"]["hum_3hour_ago"] = device_state["humidity_log"]["hum_2hour_ago"]
                    device_state["humidity_log"]["hum_4hour_ago"] = device_state["humidity_log"]["hum_3hour_ago"]
                    device_state["humidity_log"]["hum_5hour_ago"] = device_state["humidity_log"]["hum_4hour_ago"]
                    device_state["humidity_log"]["hum_6hour_ago"] = device_state["humidity_log"]["hum_5hour_ago"]
                    device_state["humidity_log"]["hum_7hour_ago"] = device_state["humidity_log"]["hum_6hour_ago"]
                    device_state["humidity_log"]["hum_8hour_ago"] = device_state["humidity_log"]["hum_7hour_ago"]
                    device_state["humidity_log"]["hum_9hour_ago"] = device_state["humidity_log"]["hum_8hour_ago"]
                    device_state["humidity_log"]["hum_10hour_ago"] = device_state["humidity_log"]["hum_9hour_ago"]
                    device_state["humidity_log"]["hum_11hour_ago"] = device_state["humidity_log"]["hum_10hour_ago"]
                    device_state["humidity_log"]["hum_12hour_ago"] = device_state["humidity_log"]["hum_11hour_ago"]
                    device_state["humidity_log"]["hum_13hour_ago"] = device_state["humidity_log"]["hum_12hour_ago"]
                    device_state["humidity_log"]["hum_14hour_ago"] = device_state["humidity_log"]["hum_13hour_ago"]
                    device_state["humidity_log"]["hum_15hour_ago"] = device_state["humidity_log"]["hum_14hour_ago"]
                    device_state["humidity_log"]["hum_16hour_ago"] = device_state["humidity_log"]["hum_15hour_ago"]
                    device_state["humidity_log"]["hum_17hour_ago"] = device_state["humidity_log"]["hum_16hour_ago"]
                    device_state["humidity_log"]["hum_18hour_ago"] = device_state["humidity_log"]["hum_17hour_ago"]
                    device_state["humidity_log"]["hum_19hour_ago"] = device_state["humidity_log"]["hum_18hour_ago"]
                    device_state["humidity_log"]["hum_20hour_ago"] = device_state["humidity_log"]["hum_19hour_ago"]
                    device_state["humidity_log"]["hum_21hour_ago"] = device_state["humidity_log"]["hum_20hour_ago"]
                    device_state["humidity_log"]["hum_22hour_ago"] = device_state["humidity_log"]["hum_21hour_ago"]
                    device_state["humidity_log"]["hum_23hour_ago"] = device_state["humidity_log"]["hum_22hour_ago"]
                    device_state["humidity_log"]["hum_24hour_ago"] = device_state["humidity_log"]["hum_23hour_ago"]
                    
                    #save new data to 1 hour ago
                    device_state["temperature_log"]["temp_1hour_ago"] = temperature
                    device_state["humidity_log"]["hum_1hour_ago"] = humidity
                
                    #push data to firebase if connected
                    if device_state["connected"]== "1":
                        #patch data to firebase
                        patch_firebase({"temperature_log": device_state["temperature_log"],
                                        "humidity_log": device_state["humidity_log"]})    
                    else: #push data to local json otherwise
                        write_state("/home/pi/device_state.json", "temperature_log", device_state["temperature_log"])
                        write_state("/home/pi/device_state.json", "humidity_log", device_state["humidity_log"])
                    
                #start clock
                sensor_log_timer = time.time()
            
            #write data and send to server after set time elapses
            if time.time() - data_timer > 5:

                if feature_toggles["save_data"] == "1":
                    #save data to .csv
                    write_csv('/home/pi/data_output/sensor_feed/sensor_data.csv',{"time": [str(time.time())], "temperature": [temperature], "humidity": [humidity], "water_low": [water_low]})

                if device_state["connected"]== "1":
                    #patch data to firebase
                    patch_firebase({"temperature": str(temperature), "humidity": str(humidity), "water_low": str(water_low)})
                else:
                    write_state("/home/pi/device_state.json", "temperature", str(temperature))
                    write_state("/home/pi/device_state.json", "humidity", str(humidity))
                    write_state("/home/pi/device_state.json", "temperature", str(humidity))
                    
                #start clock
                data_timer = time.time()
           
            #update actuators in use
            if feature_toggles["heater"] == "1":
                run_heat(str(heat_pd(temperature,int(grow_params["target_temperature"]),last_temperature,last_target_temperature,int(grow_params["P_temp"]),int(grow_params["D_temp"]))))
            if feature_toggles["humidifier"] == "1":
                run_hum(str(hum_pd(humidity,int(grow_params["target_humidity"]),last_humidity,last_target_humidity,int(grow_params["P_hum"]),int(grow_params["D_hum"]))))
            if feature_toggles["fan"] == "1":
                run_fan(fan_pd(temperature,humidity,int(grow_params["target_temperature"]),int(grow_params["target_humidity"]),last_temperature,last_humidity,last_target_temperature,last_target_humidity,int(grow_params["Pt_fan"]),int(grow_params["Ph_fan"]),int(grow_params["Dt_fan"]),int(grow_params["Dh_fan"])))
            if feature_toggles["light"] == "1":
                run_light(int(grow_params["time_start_light"]), int(grow_params["time_start_dark"]), int(grow_params["lighting_interval"]))
            if feature_toggles["camera"] == "1":
                run_camera(int(grow_params["camera_interval"]))
            if feature_toggles["water"] == "1":
                run_water(int(grow_params["watering_duration"]),int(grow_params["watering_interval"]))

            #set exit condition
            if device_state["running"] == "0":
                terminate_program()

            time.sleep(5)

    except (KeyboardInterrupt):
        terminate_program()
    except Exception as e:
        print(e)
        terminate_program()
