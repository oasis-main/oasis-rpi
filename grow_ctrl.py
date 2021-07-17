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
hum_process = None
fan_process = None
light_process = None
camera_process = None
water_process = None

#declare sensor data variables
temp = 0
hum = 0
last_temp = 0
last_hum = 0
last_targetT = 0
last_targetH = 0
waterLow = 0

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
def listen(): #Depends on 'serial', start_serial(); Modifies: ser_in, sensorInfo, temp, hum, last_temp, last_hum, waterLow
    #load in global vars
    global ser_in,sensorInfo,temp,hum,last_temp,last_hum,waterLow

    if ser_in == None:
        return

    #listen for data from aurdino
    sensorInfo = ser_in.readline().decode('UTF-8').strip().split(' ')

    if len(sensorInfo)<3:
        pass
    else:
        #print and save our data
        last_hum = hum
        hum =float(sensorInfo[0])

        last_temp = temp
        temp =float(sensorInfo[1])

        waterLow = int(sensorInfo[2])

#PD controller to modulate heater feedback
def heat_pd(temp, targetT, last_temp, last_targetT, P_heat, D_heat): #no dependencies
    err_temp = targetT-temp

    temp_dot = temp-last_temp

    targetT_dot = targetT-last_targetT

    err_dot_temp = targetT_dot-temp_dot

    heat_level  = P_heat*err_temp + D_heat*err_dot_temp
    heat_level  = max(min(int(heat_level),100),0)

    return heat_level

#PD controller to modulate humidifier feedback
def hum_pd(hum, targetH, last_hum, last_targetH, P_hum, D_hum): #no dependencies
    err_hum = targetH-hum

    hum_dot = hum-last_hum

    targetH_dot = targetH-last_targetH

    err_dot_hum = targetH_dot-hum_dot

    hum_level  = P_hum*err_hum + D_hum*err_dot_hum
    hum_level  = max(min(int(hum_level),100),0)

    return hum_level

#PD controller to modulate fan feedback
def fan_pd(temp, hum, targetT, targetH, last_temp, last_hum, last_targetT, last_targetH, Pt_fan, Ph_fan, Dt_fan, Dh_fan): #no dependencies
    err_temp = temp-targetT
    err_hum = hum-targetH

    temp_dot = temp-last_temp
    hum_dot = hum-last_hum

    targetT_dot = targetT-last_targetT
    targetH_dot = targetH-last_targetH

    err_dot_temp = temp_dot-targetT_dot
    err_dot_hum = hum_dot-targetH_dot

    fan_level  = Pt_fan*err_temp + Ph_fan*err_hum + Dt_fan*err_dot_temp + Dh_fan*err_dot_hum
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
    global hum_process

    try:
        poll_hum = hum_process.poll() #hum
        if poll_hum is not None:
            hum_process = Popen(['python3', '/home/pi/oasis-grow//humidityElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        hum_process = Popen(['python3', '/home/pi/oasis-grow//humidityElement.py', str(intensity)]) #If no process, then starts

#poll fan subprocess if applicable and relaunch/update actuators
def run_fan(intensity): #Depends on: 'subprocess'; Modifies: hum_process
    global fan_process

    try:
        poll_fan = fan_process.poll() #fan
        if poll_fan is not None:
            fan_process = Popen(['python3', '/home/pi/oasis-grow/fanElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        fan_process = Popen(['python3', '/home/pi/oasis-grow//fanElement.py', str(intensity)]) #If no process, then starts

#poll light subprocess if applicable and relaunch/update actuators
def run_light(is_light_on, time_on, time_off, refresh_frequency):
    global light_process #Depends on: 'subprocess'; Modifies: light_process

    try:
        poll_light = light_process.poll() #light
        if poll_light is not None:
            light_process = Popen(['python3', '/home/pi/oasis-grow/lightingElement.py', str(is_light_on), str(time_on), str(time_off), str(refresh_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        light_process = Popen(['python3', '/home/pi/oasis-grow//lightingElement.py', str(is_light_on), str(time_on), str(time_off), str(refresh_frequency)]) #If no process, then starts

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
def run_water(is_water_on, watering_duration, watering_frequency): #Depends on: 'subprocess'; Modifies: water_process
    global water_process

    try:
        poll_water = water_process.poll() #water
        if poll_water is not None:
            water_process = Popen(['python3', '/home/pi/oasis-grow/wateringElement.py', str(is_water_on), str(watering_duration), str(watering_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        water_process = Popen(['python3', '/home/pi/oasis-grow//wateringElement.py', str(is_water_on), str(watering_duration), str(watering_frequency)]) #If no process, then starts

#terminates the program and all running subprocesses
def terminate_program(): #Depends on: load_state(), 'sys', 'subprocess' #Modifies: heat_process, hum_process, fan_process, light_process, camera_process, water_process
    global heat_process, hum_process, fan_process, light_process, camera_process, water_process

    print("Terminating Program...")

    load_state() #get feature toggles

    if (feature_toggles["heater"] == "1") and (heat_process != None): #go through toggles and kill active processes
        heat_process.terminate()
        heat_process.wait()

    if (feature_toggles["humidifier"] == "1") and (hum_process != None):
        hum_process.terminate()
        hum_process.wait()

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

    #launch main program loop
    try:
        print("------------------------------------------------------------")

        while True:

            last_targetT = int(grow_params["targetT"]) #save last temperature and humidity targets to calculate delta for PD controllers
            last_targetH = int(grow_params["targetH"])

            load_state() #regresh the state variables to get new parameters


            if (feature_toggles["temp_hum_sensor"] == "1") or (feature_toggles["water_low_sensor"] == "1"):
                try: #attempt to read data from sensor, raise exception if there is a problem
                    listen() #this will be changed to run many sensor functions as opposed to one serial listener
                except Exception as e:
                    print(e)
                    print("Serial Port Failure")

            if feature_toggles["heater"] == "1":
                print("Target Temperature: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(int(grow_params["targetT"]),temp, heat_pd(temp,
                                                                                                                                  int(grow_params["targetT"]),
                                                                                                                                  last_temp,
                                                                                                                                  last_targetT,
                                                                                                                                  int(grow_params["P_temp"]),
                                                                                                                                  int(grow_params["D_temp"]))))
            if feature_toggles["humidifier"] == "1":
                print("Target Humidity: %.1f %% | Current: %.1f %% | Hum_PID: %s %%"%(int(grow_params["targetH"]), hum, hum_pd(hum,
                                                                                                                               int(grow_params["targetH"]),
                                                                                                                               last_hum,
                                                                                                                               last_targetH,
                                                                                                                               int(grow_params["P_hum"]),
                                                                                                                               int(grow_params["D_hum"]))))

            if feature_toggles["fan"] == "1":
                print("Fan PD: %s %%"%(fan_pd(temp,
                                              hum,
                                              int(grow_params["targetT"]),
                                              int(grow_params["targetH"]),
                                              last_temp,
                                              last_hum,
                                              last_targetT,
                                              last_targetH,
                                              int(grow_params["Pt_fan"]),
                                              int(grow_params["Ph_fan"]),
                                              int(grow_params["Dt_fan"]),
                                              int(grow_params["Dh_fan"]))))

            if feature_toggles["light"] == "1":
                print("Light Mode: %s | Turns on at: %i hours  | Turns off at: %i hours"%(grow_params["targetL"], int(grow_params["LtimeOn"]), int(grow_params["LtimeOff"])))

            if feature_toggles["camera"] == "1":
                print("Image every %i seconds"%(int(grow_params["cameraInterval"])))

            if feature_toggles["water"] == "1":
                print("Watering Mode: %s | Watering for: %i seconds  | Watering every: %i seconds"%(grow_params["waterMode"], int(grow_params["waterDuration"]), int(grow_params["waterInterval"])))

            if feature_toggles["water_low_sensor"] == "1":
                if waterLow == 1:
                    print("Water Level Low!")

            print("------------------------------------------------------------")

            #write data and send to server after set time elapses
            if time.time() - data_timer > 5:

                if feature_toggles["save_data"] == "1":
                    #save data to .csv
                    write_csv('/home/pi/data_output/sensor_feed/sensor_data.csv',{"time": [str(time.time())], "temp": [temp], "hum": [hum], "waterLow": [waterLow]})

                if device_state["connected"]== "1":
                    #patch data to firebase
                    patch_firebase({"temp": str(temp), "hum": str(hum), "waterLow": str(waterLow)})

                #start clock
                data_timer = time.time()

            if feature_toggles["heater"] == "1":
                run_heat(str(heat_pd(temp,int(grow_params["targetT"]),last_temp,last_targetT,int(grow_params["P_temp"]),int(grow_params["D_temp"]))))
            if feature_toggles["humidifier"] == "1":
                run_hum(str(hum_pd(hum,int(grow_params["targetH"]),last_hum,last_targetH,int(grow_params["P_hum"]),int(grow_params["D_hum"]))))
            if feature_toggles["fan"] == "1":
                run_fan(fan_pd(temp,hum,int(grow_params["targetT"]),int(grow_params["targetH"]),last_temp,last_hum,last_targetT,last_targetH,int(grow_params["Pt_fan"]),int(grow_params["Ph_fan"]),int(grow_params["Dt_fan"]),int(grow_params["Dh_fan"])))
            if feature_toggles["light"] == "1":
                run_light(grow_params["targetL"], int(grow_params["LtimeOn"]), int(grow_params["LtimeOff"]), int(grow_params["lightInterval"]))
            if feature_toggles["camera"] == "1":
                run_camera(int(grow_params["cameraInterval"]))
            if feature_toggles["water"] == "1":
                run_water(grow_params["waterMode"],int(grow_params["waterDuration"]),int(grow_params["waterInterval"]))

            if device_state["running"] == "0":
                terminate_program()

            time.sleep(5)

    except (KeyboardInterrupt):
        terminate_program()
    except Exception as e:
        print(e)
        terminate_program()
