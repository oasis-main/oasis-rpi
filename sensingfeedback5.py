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

#start serial RPi<-Arduino
ser = serial.Serial('/dev/ttyACM0',9600)
line = 0
sensorInfo = " "
heat = 0
hum = 0

#set PID targets
targetT = 80  #target temperature
P = 10
I = 1
D = 1

#create PID controllers
pid_temp = PID.PID(P, I, D)
pid_temp.SetPoint = targetT
pid_temp.setSampleTime(1)
pid_temp.setKp(10)
pid_temp.setKi(1)
pid_temp.setKd(1)

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
heat_process = Popen(['python', 'heatingElement.py', str(80)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

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
		try:
			start = time.time()
			requests.post('http://18.191.255.9:3000/api/heartbeat',json={'heat':heat})
			params = eval(requests.get('http://18.191.255.9:3000/api/params').content)
			targetT = params['TempDes']
			pid_temp.SetPoint = targetT
		except:
			pass

	# Set PWM expansion channel 0 to the target setting
	time.sleep(0.5)

