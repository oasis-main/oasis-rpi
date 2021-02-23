#---------------------------------------------------------------------------------------
#IMPORTS
#Shell, PID, Communication, Time
#---------------------------------------------------------------------------------------
#Setup Path
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

#Process management
import serial
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal

#PID pkgs
import PID

#communicating with firebase
import requests

#data handling
import json
import csv
import pandas

#dealing with specific times of the day
import time
import datetime

#declare state variables
device_state = None #describes the current state of the system
access_config = None #contains credentials for connecting to firebase
feature_toggles = None #tells grow_ctrl which elements are active and which are not
grow_params = None #offers run parameters to grow-ctrl

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

#save key values to .json
def write_state(path,field,value): #Depends on: load_state(), 'json'; Modifies: path
    load_state() #get connection status

    with open(path, "r+") as x: #write state to local files
        data = json.load(x)
        data[field] = value
        x.seek(0)
        json.dump(data, x)
        x.truncate()
    x.close()

#loads device state, hardware, and access configurations
def load_state(): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, modules_config, access_config, grow_params

    with open("/home/pi/device_state.json") as d:
        device_state = json.load(d) #get device state
    d.close()

    with open("/home/pi/access_config.json") as a:
        access_config = json.load(a) #get access state
    a.close()

    with open("/home/pi/grow_params.json") as g:
        grow_params = json.load(g)
    g.close()

#modifies a firebase variable
def patch_firebase(field,value): #Depends on: load_state(),'requests','json'; Modifies: database['field'], state variables
    load_state()
    data = json.dumps({field: value})
    url = "https://oasis-1757f.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)

#attempts connection to microcontroller
def start_serial(): #Depends on:'serial'; Modifies: ser_out
    global ser_in

    try:
        try:
            ser_in = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
            print("Started serial communication with Arduino Nano.")
        except:
            ser_in = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
            print("Started serial communication with Arduino Uno.")
    except Exception as e:
        ser_in = None
        print("Serial connection not found")

#gets data from serial
def listen(): #Depends on 'serial', start_serial(); Modifies: ser_in, sensorInfo, temp, hum, last_temp, last_hum, waterLow
    #load in global vars
    global ser_in,sensorInfo,temp,hum,last_temp,last_hum,waterLow

    #listen for data from aurdino
    sensorInfo = ser_in.readline().decode('UTF-8').strip().split(' ')
    #print(sensorInfo)

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
    err_temp = temp-targetT

    temp_dot = temp-last_temp

    targetT_dot = targetT-last_targetT

    err_dot_temp = temp_dot-targetT_dot

    heat_level  = P_heat*err_temp + D_heat*err_dot_temp
    heat_level  = max(min(int(heat_level),100),0)

    return heat_level

#PD controller to modulate humidifier feedback
def hum_pd(hum, targetH, last_hum, last_targetH, P_hum, D_hum): #no dependencies
    err_hum = hum-targetH

    hum_dot = hum-last_hum

    targetH_dot = targetH-last_targetH

    err_dot_hum = hum_dot-targetH_dot

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

if __name__ == '__main__':
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
        #continue with program execution
        pass



else:
    print("please offer valid run parameters")
    sys.exit()
