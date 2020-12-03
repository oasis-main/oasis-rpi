#---------------------------------------------------------------------------------------
#IMPORTS
#Shell, PID, Communication, Time
#---------------------------------------------------------------------------------------
#Setup Path
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

#Shell pkgs
import serial
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal

#PID pkgs
import PID

#communicating with firebase
import requests
import json

#dealing with specific times of the day
import time
import datetime

#-----------------------------------------------------------------------------
#Exit early if opening subprocess daemon
#-----------------------------------------------------------------------------

if str(sys.argv[1]) == "daemon":
    print("grow_ctrl daemon started")
    #log daemon start
    with open('/home/pi//logs/growCtrl_log.json', 'r+') as l:
        log = json.load(l)
        log['last_start_mode'] = "daemon" # <--- add `id` value.
        l.seek(0) # <--- should reset file position to the beginning.
        json.dump(log, l)
        l.truncate() # remove remaining part
    l.close()
    sys.exit()
if str(sys.argv[1]) == "main":
    print("grow_ctrl main started")
    #log main start
    with open('/home/pi/logs/growCtrl_log.json', 'r+') as l:
        log = json.load(l)
        log['last_start_mode'] = "main" # <--- add `id` value.
        l.seek(0) # <--- should reset file position to the beginning.
        json.dump(log, l)
        l.truncate() # remove remaining part
    l.close
else:
    print("please offer valid run parameters")
    sys.exit()

#---------------------------------------------------------------------------------------
#INITIALIZATION
#setting up variables, sensors, controlers, database
#---------------------------------------------------------------------------------------

#initialize firebase

#try:
    #use refresh token to get new id token
    #id_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjBlM2FlZWUyYjVjMDhjMGMyODFhNGZmN2RjMmRmOGIyMzgyOGQ1YzYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vb2FzaXMtMTc1N2YiLCJhdWQiOiJvYXNpcy0xNzU3ZiIsImF1dGhfdGltZSI6MTYwMzM5NzgyNywidXNlcl9pZCI6InhmZGZoeHdaZEJkZmZVdnc2N1ZVSnpIeVFuMzIiLCJzdWIiOiJ4ZmRmaHh3WmRCZGZmVXZ3NjdWVUp6SHlRbjMyIiwiaWF0IjoxNjAzMzk4MDA1LCJleHAiOjE2MDM0MDE2MDUsImVtYWlsIjoiYXNkZkBhc2RmLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJhc2RmQGFzZGYuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.khg2Z2rlkzdUXuk1cznuutPMLN9CDl2z7OlirlNQSorGMxzD7fGjEwGNRXAPhJlRQEBKhhfjuTmR736gL4Gz1SA_4KOWQCbDeg76ru_DHnB8ZdJoDP6gYs1vsDxgQN2vp2gDY9zW4Go_Cl7lVgdWAdNsG0_CKXLXt28fStsmKVdotCFrSHDZa3j0Q45Q4vIr1aFHB74vjRLQrftULI9-b7tdkNkRBYKVLTYq1xnVtmRbQRbYSoI0Xge2H82oDaZN0KM58tPvH-t5s5Z0xdE1NOWNJFbqvgjQFWqPeaSs53B4hIApr1t_LUUVlGwZfn34txV8koUcrJbMRNw1vkPoCQ"
    #local_id = "xfdfhxwZdBdffUvw67VUJzHyQn32"

    #get database data
    #result = requests.get("https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+ str(id_token))
    #data = json.loads(result.content.decode())
    #print("Firebase Initialization: SUCCESS")
    #print(data)

#    def get_from_firebase(id_token,local_id, data_name):
#        result = requests.get("https://oasis-1757f.firebaseio.com/"+str(local_id)+"/"+str(data_name)+".json?auth="+str(id_token))
#        data = json.loads(result.content.decode())
#        return data
#except Exception as e:
#    print("Firebase Initialization: FAILURE")
#    print(e)

#start serial RPi<-Arduino
ser_in = serial.Serial('/dev/ttyUSB0',9600)
line = 0
sensorInfo = " "

#place holder for sensor data
temp = 0
hum = 0
waterLow = 0

#import grow_params
with open('/home/pi/grow_params.json', "r+") as g:
  grow_params = json.load(g)
g.close()


#load grow parameters
targetT = int(grow_params["targetT"])  #temperature set to?
targetH = int(grow_params["targetH"]) #humidity set to?
targetL = grow_params["targetL"] #lights on yes or no?
LtimeOn = int(grow_params["LtimeOn"]) #when turn on 0-23 hr time?
LtimeOff = int(grow_params["LtimeOff"]) #when turn off 0-23 hr time?
lightInterval = int(grow_params["lightInterval"]) #how long until update?
cameraInterval = int(grow_params["cameraInterval"]) #how long until next pic?
waterMode = grow_params["waterMode"] #watering on yes or no?
waterDuration = int(grow_params["waterDuration"]) #how long water?
waterInterval = int(grow_params["waterInterval"]) #how often water?

#initialize actuator subprocesses
#heater: params = on/off frequency
heat_process = Popen(['python3', '/home/pi/grow-ctrl/heatingElement.py', str(0)])
#humidifier: params = on/off frequency
hum_process = Popen(['python3', '/home/pi/grow-ctrl/humidityElement.py', str(0)])
#fan: params = on/off frequency
fan_process = Popen(['python3', '/home/pi/grow-ctrl/fanElement.py', '100'])
#light & camera: params = light mode, time on, time off, interval
light_process = Popen(['python3', '/home/pi/grow-ctrl/lightingElement.py', 'on', '0', '0', '10'])
#camera: params = interval
camera_process = Popen(['python3', '/home/pi/grow-ctrl/cameraElement.py', '10'])
#watering: params = mode duration interval
water_process = Popen(['python3', '/home/pi/grow-ctrl/wateringElement.py', 'off', '0', '10'])

#create controllers:

#heater: PID Library on temperature
P_temp = 75
I_temp = 0
D_temp = 1

pid_temp = PID.PID(P_temp, I_temp, D_temp)
pid_temp.SetPoint = targetT
pid_temp.setSampleTime(1)

#humidifier: PID library on humidity
P_hum = 50
I_hum = 0
D_hum = 5

pid_hum = PID.PID(P_hum, I_hum, D_hum)
pid_hum.SetPoint = targetH
pid_hum.setSampleTime(1)

#fan: custom proportional and derivative gain on both temperature and humidity
last_temp = 0
last_hum = 0
last_targetT = 0
last_targetH = 0

Kpt = 60
Kph = 1100
Kdt = 1
Kdh = 20

def fan_pd(temp, hum, targetT, targetH, last_temp, last_hum, last_targetT, last_targetH, Kpt, Kph, Kdt, Kdh):
    err_temp = temp-targetT
    err_hum = hum-targetH

    temp_dot = temp-last_temp
    hum_dot = hum-last_hum

    targetT_dot = targetT-last_targetT
    targetH_dot = targetH-last_targetH

    err_dot_temp = temp_dot-targetT_dot
    err_dot_hum = hum_dot-targetH_dot

    fan_level  = Kpt*err_temp+Kph*err_hum+Kdt*err_dot_temp+err_hum+Kdh*err_dot_hum
    fan_level  = max(min(int(fan_level),100),0)

    return fan_level


#---------------------------------------------------------------------------------------
# Listen
#---------------------------------------------------------------------------------------

#define event listener to collect data and kick off the transfer
def listen():
    #load in global vars
    global line,ser_in,sensorInfo,temp,hum,last_temp,last_hum,waterLow

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

#start the clock for timimg data exchanges with server
start = time.time()


#---------------------------------------------------------------------------------------
#MAIN LOOP
#listen, update, show, send, receive, actuate, wait, -- else die
#
#TODO:
#	Generalize IP
#	Consolidate Shutdown processes and energy managment
#	Energy Meter (for both us and users)
#---------------------------------------------------------------------------------------

try:
    while True:
        #initialize program
        try:
            listen()
        except Exception as e:
            print(e)
            print("Serial Port Failure")

        #feed the data into our PIDs
        pid_temp.update(temp)
        pid_hum.update(hum)

        #Controller response
        tempPID_out = pid_temp.output
        tempPID_out = max( min( int(tempPID_out), 100 ),0)
        print("Target Temperature: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(targetT, temp, tempPID_out))

        humPID_out = pid_hum.output
        humPID_out = max( min( int(humPID_out), 100 ),0)
        print("Target Humidity: %.1f %% | Current: %.1f %% | Hum_PID: %s %%"%(targetH, hum, humPID_out))

        fanPD_out = fan_pd(temp, hum, targetT, targetH, last_temp, last_hum, last_targetT, last_targetH, Kpt, Kph, Kdt, Kdh)
        print("Fan PD: %s %%"%(fanPD_out))

        if targetL == "on":
            print("Light Mode: %s | Turns on at: %i hours  | Turns off at: %i hours"%(targetL, LtimeOn, LtimeOff))
        else:
            print("Light Mode: %s "%(targetL))

        if waterLow == 1:
            print("Water Level Low!")

        print("Image every %i seconds"%(cameraInterval))
        print("------------------------------------------------------------")

        #exchange data with server after set time elapses
        if time.time() - start > 5:
            #get device_state
            with open('/home/pi/device_state.json') as d:
                device_state = json.load(d)
            d.close()
            if device_state["connected"] == "1":
                try:
                    #start clock
                    start = time.time()

                    #sensor data out, needs editin
                    #url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
                    #data = json.dumps({"temp": str(int(temp)), "humid": str(int(hum)), "waterLow": str(int(waterLow))})
                    #result = requests.patch(url,data)
                    #print(result)

                    #pass old targets to derivative bank and update
                    last_targetT = targetT
                    last_targetH = targetH

                    #refresh grow_params
                    with open('/home/pi/grow_params.json') as g:
                        grow_params = json.load(g)
                    g.close()

                    #load grow parameters
                    targetT = int(grow_params["targetT"])  #temperature set to?
                    targetH = int(grow_params["targetH"]) #humidity set to?
                    targetL = grow_params["targetL"] #lights on yes or no?
                    LtimeOn = int(grow_params["LtimeOn"]) #when turn on 0-23 hr time?
                    LtimeOff = int(grow_params["LtimeOff"]) #when turn off 0-23 hr time?
                    lightInterval = int(grow_params["lightInterval"]) #how long until update?
                    cameraInterval = int(grow_params["cameraInterval"]) #how long until next pic?
                    waterMode = grow_params["waterMode"] #watering on yes or no?
                    waterDuration = int(grow_params["waterDuration"]) #how long water?
                    waterInterval = int(grow_params["waterInterval"]) #how often water?

                    #change PID module setpoints to target
                    pid_temp.SetPoint = targetT
                    pid_hum.SetPoint = targetH

                except (KeyboardInterrupt):
                    print(" ")
                    print("Terminating Program...")
                    heat_process.kill()
                    heat_process.wait()
                    hum_process.kill()
                    hum_process.wait()
                    fan_process.kill()
                    fan_process.wait()
                    light_process.kill()
                    light_process.wait()
                    camera_process.kill()
                    camera_process.wait()
                    water_process.kill()
                    water_process.wait()
                    sys.exit()
                except Exception as e:
                    print(e)
                    pass


            #poll subprocesses if applicable and relaunch/update actuators
            poll_heat = heat_process.poll() #heat
            if poll_heat is not None:
                heat_process = Popen(['python3', '/home/pi/grow-ctrl/heatingElement.py', str(tempPID_out)])

            poll_hum = hum_process.poll() #hum
            if poll_hum is not None:
                hum_process = Popen(['python3', '/home/pi/grow-ctrl/humidityElement.py', str(humPID_out)])

            poll_fan = fan_process.poll() #fan
            if poll_fan is not None:
                fan_process = Popen(['python3', '/home/pi/grow-ctrl/fanElement.py', str(fanPD_out)])

            poll_light = light_process.poll() #light
            if poll_light is not None:
                light_process = Popen(['python3', '/home/pi/grow-ctrl/lightingElement.py', str(targetL), str(LtimeOn), str(LtimeOff), str(lightInterval)])

            poll_camera = camera_process.poll() #camera
            if poll_camera is not None:
                camera_process = Popen(['python3', '/home/pi/grow-ctrl/cameraElement.py', str(cameraInterval)])

            poll_water = water_process.poll() #light
            if poll_water is not None:
                water_process = Popen(['python3', '/home/pi/grow-ctrl/wateringElement.py', str(waterMode), str(waterDuration), str(waterInterval)])

            #line marks one interation of main loop
            time.sleep(0.5)

except Exception as e:
    print(e)
    print(" ")
    print("Terminating Program...")
    heat_process.kill()
    heat_process.wait()
    hum_process.kill()
    hum_process.wait()
    fan_process.kill()
    fan_process.wait()
    light_process.kill()
    light_process.wait()
    camera_process.kill()
    camera_process.wait()
    water_process.kill()
    water_process.wait()
    sys.exit()

