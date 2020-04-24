#Sensor pkgs
import serial
import time
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT

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
temp = 0
hum = 0

#initialize actuator subprocesses
heat_process = Popen(['python', 'heatingElement.py', '0'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
hum_process = Popen(['python', 'humidityElement.py', '0'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
fan_process = Popen(['python', 'fanElement.py', '100'], stdout=PIPE, stdin=PIPE, stderr=PIPE)

#set PID targets
targetT = 70  #target temperature
P_temp = 30
I_temp = 0
D_temp = 1

targetH = 50  #target humidity
P_hum = 1
I_hum = 0
D_hum = 15

#create controllers
pid_temp = PID.PID(P_temp, I_temp, D_temp) #heating element: pid
pid_temp.SetPoint = targetT
pid_temp.setSampleTime(1)

pid_hum = PID.PID(P_hum, I_hum, D_hum) #humidity element: pid
pid_hum.SetPoint = targetH
pid_hum.setSampleTime(1)

#fan: weighted average pd
last_temp = 0
last_hum = 0
last_targetT = 0
last_targetH = 0

Kpt = 5
Kph = 50
Kdt = 1
Kdh = .5

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

#define event listener to collect data and kick off the transfer
def listen():

    global line,ser,sensorInfo,temp,hum,last_temp,last_hum #load in global vars

    if(ser.in_waiting > 0): #listen for data
        sensorInfo = str.strip(ser.readline()).split(' ')
    if len(sensorInfo)<2:
        pass
    else:
        #print(sensorInfo) #print and save our data
        last_hum = hum
	last_temp = temp
	hum =float(sensorInfo[0])
        temp =float(sensorInfo[1])

        ser.reset_input_buffer()

#start the clock
start = time.time()

#start the loop
try:
	while 1:
		#initialize program
		listen()

		#feed the data into our PID
		pid_temp.update(temp)
		pid_hum.update(hum)

		#PID response
		tempPID_out = pid_temp.output
		tempPID_out = max( min( int(tempPID_out), 100 ),0)
		print "Target Temperature: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(targetT, temp, tempPID_out)

		humPID_out = pid_hum.output
        	humPID_out = max( min( int(humPID_out), 100 ),0)
        	print "Target Humidity: %.1f %% | Current: %.1f %% | Hum_PID: %s %%"%(targetH, hum, humPID_out)

		fanPD_out = fan_pd(temp, hum, targetT, targetH, last_temp, last_hum, last_targetT, last_targetH, Kpt, Kph, Kdt, Kdh)
		print "Fan_PD: %s %%"%(fanPD_out)

		#exchange data with server
		if time.time() - start > 5:
			try:
				#start clock
				start = time.time()
				#data out
				requests.post('http://184.72.68.192:3000/api/heartbeat', json={'temp':temp, 'hum':hum}, timeout=10)
				#parameters in
				params = requests.get('http://184.72.68.192:3000/api/params', timeout=10).json()
				#pass old targets to derivative bank and update
				last_targetT = targetT
				last_targetH = targetH
				targetT = params['tempDes']
				targetH = params['humDes']
				#change setpoints to target
				pid_temp.SetPoint = targetT
				pid_hum.SetPoint = targetH
			except:
				pass


		#poll subprocesses and relaunch if necessary
		poll_heat = heat_process.poll()
		if poll_heat is not None:
			heat_process = Popen(['python', 'heatingElement.py', str(tempPID_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

		poll_hum = hum_process.poll()
                if poll_hum is not None:
			hum_process = Popen(['python', 'humidityElement.py', str(humPID_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)

		poll_fan = fan_process.poll()
		if poll_fan is not None:
                        fan_process = Popen(['python', 'fanElement.py', str(fanPD_out)], stdout=PIPE, stdin=PIPE, stderr=PIPE)


		#line marks one interation of main loop
		print '----------------------------------------'
		time.sleep(0.5)

except KeyboardInterrupt:
	heat_process.terminate()
	heat_process.wait()
	hum_process.terminate()
	hum_process.wait()
	fan_process.terminate()
        fan_process.wait()
