#---------------------------------------------------------------------------------------
#Manages Hardware for Heating
#TODO:
#	(possible) define one function to handle various behavior
#---------------------------------------------------------------------------------------

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

import RPi.GPIO as GPIO
import time
import json

#get hardware config
with open('/home/pi/hardware_config.json') as h:
  hardware_config = json.load(h)

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Heat_GPIO = hardware_config["actuatorGPIOmap"]["heatingElement"] #heater pin pulls from config file
GPIO.setup(Heat_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(Heat_GPIO, GPIO.LOW)

#define a function making PID discrete & actuate element accordingly
def actuate(tempCtrl):
    if (tempCtrl >= 0) and (tempCtrl < 1):
        #print("level 0")
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(5)

    if (tempCtrl >= 1) and (tempCtrl < 10):
        #print("level 1")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(1) #on for 1
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 10) and (tempCtrl < 20):
        #print("level 2")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(2) #on for 2
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 20) and (tempCtrl < 30):
        #print("level 3")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(3) #on for 3
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 30) and (tempCtrl < 40):
        #print("level 4")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(4) #on for 4
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 40) and (tempCtrl < 50):
        #print("level 5")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(5) #on for 5
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 50) and (tempCtrl < 60):
        #print("level 6")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(6) #on for 6
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 60) and (tempCtrl < 70):
        #print("level 7")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(7) #on for 7
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 70) and (tempCtrl < 80):
        #print("level 8")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(8) #on for 8
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 80) and (tempCtrl < 90):
        #print("level 9")
        GPIO.output(Heat_GPIO, GPIO.HIGH)
        time.sleep(9) #on for 9
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (tempCtrl >= 90) and (tempCtrl <= 100):
        #print("level 10")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(10) #on for 10

try:
    actuate(float(sys.argv[1])) #trigger appropriate response
    GPIO.cleanup()
except:
    print("Interrupted")
    GPIO.cleanup()
