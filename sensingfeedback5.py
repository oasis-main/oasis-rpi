#Sensor pkgs
import serial
import time
import subprocess32
from subprocess import Popen, PIPE, STDOUT

#PID pkgs
import PID
import time
import os.path

#communicating with AWS
import requests

#mechanism for PID outputs
import json

#refresh pid_output bank
feedback_levels = {'heat':0}

#start serial RPi<-Arduino
ser = serial.Serial('/dev/ttyACM0',9600)
line = 0
sensorInfo = " "
heat = 0
hum = 0

#set PID targets
targetT = 76  #target temperature
P_temp = 20
I_temp = .5
D_temp = .5

#create PID controllers
pid_temp = PID.PID(P_temp, I_temp, D_temp)
pid_temp.SetPoint = targetT
pid_temp.setSampleTime(1)
#pid_temp.setKp(10)
#pid_temp.setKi(1)
#pid_temp.setKd(1)

#define operating functions
def listen():

    global line,ser,sensorInfo,heat,hum #load in global vars

    if(ser.in_waiting > 0): #listen for data
        sensorInfo = str.strip(ser.readline()).split(' ')
    if len(sensorInfo)<2:
        pass
    else:
        print(sensorInfo) #print and save our data
        hum =float(sensorInfo[0])
        heat =float(sensorInfo[1])

        ser.reset_input_buffer()

#start clock
start = time.time()

#launch actuator subprocesses
heat_process = Popen(['python', 'heatingElement.py'], stdout=PIPE, stdin=PIPE, stderr=PIPE)

#start the loop
while 1:
	#initialize program
	listen()

	#feed the data into our PID
	pid_temp.update(heat)

	#PID response
	#temp:
	tempPID_out = pid_temp.output
	tempPID_out = max(min( int(tempPID_out), 100 ),0)
	print "Target: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(targetT, heat, tempPID_out)

	if time.time() - start > 5:

		start = time.time()

		try:
			requests.post('http://18.218.2.179:3000/api/heartbeat',json={'heat':heat})
			params = eval(requests.get('http://18.218.2.179:3000/api/params').content)
			targetT = params['TempDes']
			pid_temp.SetPoint = targetT
		except:
			pass

	#update json with pid feedback so they can be read into actuators
	feedback_levels = {'heat': tempPID_out}

	with open('pid_out.json', 'w') as pid_out:
    		json.dump(feedback_levels, pid_out)

	#Set PWM expansion channel 0 to the target setting (what is this?)
	time.sleep(0.5) #(what is this?)

