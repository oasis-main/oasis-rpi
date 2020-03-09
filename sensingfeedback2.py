#Sensor pkgs
import serial
import time
import subprocess

#PID pkgs
import PID
import time
import os.path

#Actuator pkgs
import RPi.GPIO as GPIO

#start serial RPi<-Arduino
ser = serial.Serial('/dev/ttyACM0',9600)
line = 0
sensorInfo = " "
heat = 0

#set PID targets
targetT = 90
P = 10
I = 1
D = 1

#create PID controller
pid = PID.PID(P, I, D)
pid.SetPoint = targetT
pid.setSampleTime(1)

#define operating functions
def condisionReport(hum, heat): #summarize conditions
    #humidity
    if hum > 75:
        print('moist')
    elif hum <  25:
        print('dry')
    else:
        print('normal humidity')


    #heat
    if heat > 90:
        print('hot')
    elif heat < 50:
        print('cold')
    else:
        print('normal temp')

def listen():

    global line,ser,sensorInfo,heat #load in global vars

    if(ser.in_waiting > 0): #listen for data
    	print('----')
        sensorInfo = str.strip(ser.readline()).split(' ')
    if len(sensorInfo)<2:
        pass
    else:
        print(sensorInfo) #print and save out data
        hum =float( sensorInfo[0])
        heat = float(sensorInfo[1])
        condisionReport(hum, heat) #summary, consider removing)

        ser.reset_input_buffer()

def readConfig (): #PID config 1
	global targetT
	with open ('/tmp/pid.conf', 'r') as f:
		config = f.readline().split(',')
		pid.SetPoint = float(config[0])
		targetT = pid.SetPoint
		pid.setKp (float(config[1]))
		pid.setKi (float(config[2]))
		pid.setKd (float(config[3]))

def createConfig (): #PID config 2
	if not os.path.isfile('/tmp/pid.conf'):
		with open ('/tmp/pid.conf', 'w') as f:
			f.write('%s,%s,%s,%s'%(targetT,P,I,D))

def heatingElement(heatPID_in): #update state of heating module
	print 'Updating State of Heating Element...'
	print heatPID_in
	#call a python script subprocess, passing heatPID_in as the magnitude

#configure and launch program
createConfig()

while 1:
	#initialize program
	listen()
	readConfig()

	#read data
	temperature = heat

	#feed into PID
	pid.update(temperature)

	#PID response
	#temp:
	tempPID_out = pid.output
	tempPID_out = max(min( int(tempPID_out), 100 ),0)
	print "Target: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(targetT, temperature, tempPID_out)

	#call actuator subprocesses with PID as input
	heatingElement(tempPID_out)

	# Set PWM expansion channel 0 to the target setting
	time.sleep(0.5)
