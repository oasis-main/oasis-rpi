#---------------------------------------------------------------------------------------
#Manages Hardware for Humidity 
#TODO:
# - generalize IP, pass in as argumen from main file and take as input function to
# - functionalize image capture and posting capability
# - adjust light timing to allow for and type of window
#---------------------------------------------------------------------------------------

#import libraries
import sys
import RPi.GPIO as GPIO
import time
import datetime
import base64
import requests
from PIL import Image
import os
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT

#hardware setup
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Light_GPIO = 17 #light is going to be triggered with pin 17
GPIO.setup(Light_GPIO, GPIO.OUT) #GPIO setup relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function to actuate element
def actuate(lightingMode, timeOn = 0, timeOff = 0, interval = 0): #time on must be less than time off

	now = datetime.datetime.now()
	HoD = now.hour

	ip = '54.172.134.78'
        port = 3000
        image_path = '/home/pi/Desktop/output.jpg'

	if lightingMode == "off":
		GPIO.output(Light_GPIO, GPIO.LOW) #light on (relay closed)
        	still = Popen('sudo raspistill -o ~/Desktop/output.jpg', stdout = None, shell = True) #snap: call the camera
        	still.wait()
		GPIO.output(Light_GPIO, GPIO.HIGH) #light off (relay open)
		if image_path != '':
                	with open(image_path, 'rb') as imageFile:
                        	image_data = base64.b64encode(imageFile.read()) #encode in base64 for sending
        	else:
                	print('fail')
                	image_data = 'custom_image' #TODO: remove from code if useless
        	
		json={'image':image_data}
        	
        	try:
			requests.post('http://'+ip+':'+str(port)+'/upload/image', json, timeout=20) #send: post to /upload/image endpoint
		except: 
    			pass
		time.sleep(interval)
	if lightingMode == "on":
		if HoD >= timeOn and HoD < timeOff:
			GPIO.output(Light_GPIO, GPIO.LOW) #light on (relay closed)
                	still = Popen('sudo raspistill -o ~/Desktop/output.jpg', stdout = None, shell = True) #snap: call the camera
                	still.wait()
                	if image_path != '':
                        	with open(image_path, 'rb') as imageFile:
                                	image_data = base64.b64encode(imageFile.read()) #encode in base64 for sending
                	else:
                        	print('fail')
                        	image_data = 'custom_image' #remember to verify this is necessary
                	
			json={'image':image_data}
                	
                	try:
				requests.post('http://'+ip+':'+str(port)+'/upload/image', json, timeout=20) #send: post to /upload/image endpoint
                	except: 
    				pass
			time.sleep(interval)
		if HoD < timeOn or HoD >= timeOff:
                        GPIO.output(Light_GPIO, GPIO.LOW) #light on (relay closed)
                        still = Popen('sudo raspistill -o ~/Desktop/output.jpg', stdout = None, shell = True) #snap: call the camera
                        still.wait()
			GPIO.output(Light_GPIO, GPIO.HIGH) #light off (relay open)
                        if image_path != '':
                                with open(image_path, 'rb') as imageFile:
                                        image_data = base64.b64encode(imageFile.read()) #encode in base64 for sending
                        else:
                                print('fail')
                                image_data = 'custom_image'
                        json={'image':image_data}
                        #print(image_data)
                        try:
				requests.post('http://'+ip+':'+str(port)+'/upload/image', json, timeout=20) #send: post to /upload/image endpoint
                        except: 
    				pass
			time.sleep(interval)

try:
        actuate(str(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        GPIO.cleanup()
except KeyboardInterrupt:
        print 'Interrupted'
        GPIO.cleanup()

