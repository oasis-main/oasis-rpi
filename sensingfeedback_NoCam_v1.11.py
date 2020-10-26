#TODO:
#- add circle-lights
#- integrate with firebase user-data scheme

#---------------------------------------------------------------------------------------
#IMPORTS
#Shell, PID, Communication, Time
#---------------------------------------------------------------------------------------

#Shell pkgs
import serial
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT
import os
import os.path
import signal
import sys

#PID pkgs
import PID

#communicating with firebase
import requests
import json

#dealing with specific times of the day
import time
import datetime

#---------------------------------------------------------------------------------------
#INITIALIZATION
#setting up variables, sensors, controlers, database
#---------------------------------------------------------------------------------------

#initialize firebase

try:
    #use refresh token to get new id token
    id_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjBlM2FlZWUyYjVjMDhjMGMyODFhNGZmN2RjMmRmOGIyMzgyOGQ1YzYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vb2FzaXMtMTc1N2YiLCJhdWQiOiJvYXNpcy0xNzU3ZiIsImF1dGhfdGltZSI6MTYwMzM5NzgyNywidXNlcl9pZCI6InhmZGZoeHdaZEJkZmZVdnc2N1ZVSnpIeVFuMzIiLCJzdWIiOiJ4ZmRmaHh3WmRCZGZmVXZ3NjdWVUp6SHlRbjMyIiwiaWF0IjoxNjAzMzk4MDA1LCJleHAiOjE2MDM0MDE2MDUsImVtYWlsIjoiYXNkZkBhc2RmLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJhc2RmQGFzZGYuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.khg2Z2rlkzdUXuk1cznuutPMLN9CDl2z7OlirlNQSorGMxzD7fGjEwGNRXAPhJlRQEBKhhfjuTmR736gL4Gz1SA_4KOWQCbDeg76ru_DHnB8ZdJoDP6gYs1vsDxgQN2vp2gDY9zW4Go_Cl7lVgdWAdNsG0_CKXLXt28fStsmKVdotCFrSHDZa3j0Q45Q4vIr1aFHB74vjRLQrftULI9-b7tdkNkRBYKVLTYq1xnVtmRbQRbYSoI0Xge2H82oDaZN0KM58tPvH-t5s5Z0xdE1NOWNJFbqvgjQFWqPeaSs53B4hIApr1t_LUUVlGwZfn34txV8koUcrJbMRNw1vkPoCQ"
    local_id = "xfdfhxwZdBdffUvw67VUJzHyQn32"

    #get database data
    #result = requests.get("https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+ str(id_token))
    #data = json.loads(result.content.decode())
    #print("Firebase Initialization: SUCCESS")
    #print(data)

    def get_from_firebase(id_token,local_id, data_name):
        result = requests.get("https://oasis-1757f.firebaseio.com/"+str(local_id)+"/"+str(data_name)+".json?auth="+str(id_token))
        data = json.loads(result.content.decode())
        return data
except Exception as e:
    print("Firebase Initialization: FAILURE")
    print(e)

#start serial RPi<-Arduino
ser = serial.Serial('/dev/ttyUSB0',9600)
line = 0
sensorInfo = " "

#place holder for sensor data
temp = 0
hum = 0
waterLow = 0

#placeholder for set parameter  targets
targetT = 75  #target temperature
targetH = 90  #target humidity
targetL = "off" #light mode
LtimeOn = 8
LtimeOff = 20
lightInterval = 60
cameraInterval = 3600
waterMode = "off"
waterDuration = 15
waterInterval = 3600

#initialize actuator subprocesses
#heater: params = on/off frequency
heat_process = Popen(['python3', 'heatingElement.py', str(0)], stdout=PIPE, stdin=PIPE, stderr=PIPE)
#humidifier: params = on/off frequency
hum_process = Popen(['python3', 'humidityElement.py', str(0)], stdout=PIPE, stdin=PIPE, stderr=PIPE)
#fan: params = on/off frequency
fan_process = Popen(['python3', 'fanElement.py', '100'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
#light & camera: params = light mode, time on, time off, interval
light_process = Popen(['python3', 'lightingElement.py', 'on', '0', '0', '10'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
#camera: params = interval
#camera_process = Popen(['python3', 'cameraElement.py', '10'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
#watering: params = mode duration interval
water_process = Popen(['python3', 'wateringElement.py', 'off', '0', '10'], stdout=PIPE, stdin=PIPE, stderr=PIPE)

#create controllers:

#heater: PID Library on temperature
P_temp = 75
I_temp = 0
D_temp = 1

pid_temp = PID.PID(P_temp, I_temp, D_temp)
pid_temp.SetPoint = targetT
pid_temp.setSampleTime(1)

#humidifier: PID library on humidity
P_hum = 25
I_hum = 0
D_hum = 10

pid_hum = PID.PID(P_hum, I_hum, D_hum)
pid_hum.SetPoint = targetH
pid_hum.setSampleTime(1)

#fan: custom proportional and derivative gain on both temperature and humidity
last_temp = 0
last_hum = 0
last_targetT = 0
last_targetH = 0

Kpt = 50
Kph = 1000
Kdt = 1
Kdh = 15

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
    global line,ser,sensorInfo,temp,hum,last_temp,last_hum,waterLow

    #listen for data from aurdino
    sensorInfo = ser.readline().decode('UTF-8').strip().split(' ')
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

        print("Camera every %i seconds"%(cameraInterval))
        print("------------------------------------------------------------")

        #exchange data with server after set time elapses
        if time.time() - start > 5:
            try:
                #start clock
                start = time.time()

                #sensor data out
                url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
                data = json.dumps({"temp": str(int(temp)), "humid": str(int(hum)), "waterLow": str(int(waterLow))})
                result = requests.patch(url,data)
                print(result)

                #pass old targets to derivative bank and update
                last_targetT = targetT
                last_targetH = targetH

                targetT = get_from_firebase(id_token, local_id, 'set_temp')['set_temp'] #last argumentmust be an explicit string
                targetH = get_from_firebase(id_token, local_id, 'set_humid')['set_humid']
                targetL = get_from_firebase(id_token, local_id, 'light_mode')['light_mode']
                LtimeOn = get_from_firebase(id_token, local_id, 'light_time_on')['light_time_on']
                LtimeOff = get_from_firebase(id_token, local_id, 'light_time_off')['light_time_off']
                waterMode = get_from_firebase(id_token, local_id, 'water_mode')['water_mode']
                waterDuration = get_from_firebase(id_token, local_id, 'water_duration')['water_duration']
                waterInterval = get_from_firebase(id_token, local_id, 'water_interval')['water_interval']

                #cameraInterval = params['cameraInterval']
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
                #camera_process.kill()
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
                heat_process = Popen(['python3', 'heatingElement.py', str(tempPID_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

            poll_hum = hum_process.poll() #hum
            if poll_hum is not None:
                hum_process = Popen(['python3', 'humidityElement.py', str(humPID_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

            poll_fan = fan_process.poll() #fan
            if poll_fan is not None:
                fan_process = Popen(['python3', 'fanElement.py', str(fanPD_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

            poll_light = light_process.poll() #light
            if poll_light is not None:
                light_process = Popen(['python3', 'lightingElement.py', str(targetL), str(LtimeOn), str(LtimeOff), str(lightInterval)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

            #poll_camera = camera_process.poll() #camera
            #if poll_camera is not None:
            #    camera_process = Popen(['python3', 'cameraElement.py', str(cameraInterval)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

            poll_water = water_process.poll() #light
            if poll_water is not None:
                water_process = Popen(['python3', 'wateringElement.py', str(waterMode), str(waterDuration), str(waterInterval)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

            #line marks one interation of main loop
            #print('Tx/Rx Confirmed')
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
    #camera_process.kill()
    #camera_process.wait()
    water_process.kill()
    water_process.wait()
    sys.exit()

