#---------------------------------------------------------------------------------------
#Manages Hardware for Fans / Ventilation
#---------------------------------------------------------------------------------------

#import shell modules
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

import RPi.GPIO as GPIO
import time
import json
from utils import concurrent_state as cs

#get hardware config
cs.load_state()

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Fan_GPIO = cs.hardware_config["actuator_gpio_map"]["fan_relay"] #heater pin pulls from config file
GPIO.setup(Fan_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(Fan_GPIO, GPIO.LOW)

#define a function making PID discrete & actuate element accordingly
def actuate_pid(fan_ctrl):
    if (fan_ctrl >= 0) and (fan_ctrl < 1):
        #print("level 0")
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1)

    if (fan_ctrl >= 1) and (fan_ctrl < 10):
        #print("level 1")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(1) #on for 1
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 10) and (fan_ctrl < 20):
        #print("level 2")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(2) #on for 2
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 20) and (fan_ctrl < 30):
        #print("level 3")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(3) #on for 3
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 30) and (fan_ctrl < 40):
        #print("level 4")
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(4) #on for 4
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 40) and (fan_ctrl < 50):
        #print("level 5")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(5) #on for 5
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 50) and (fan_ctrl < 60):
        #print("level 6")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(6) #on for 6
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 60) and (fan_ctrl < 70):
        #print("level 7")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(7) #on for 7
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 70) and (fan_ctrl < 80):
        #print("level 8")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(8) #on for 8
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 80) and (fan_ctrl < 90):
        #print("level 9")
        GPIO.output(Fan_GPIO, GPIO.HIGH)
        time.sleep(9) #on for 9
        GPIO.output(Fan_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (fan_ctrl >= 90) and (fan_ctrl <= 100):
        #print("level 10")
        GPIO.output(Fan_GPIO,GPIO.HIGH)
        time.sleep(10) #on for 10

def actuate_interval(duration = 1, interval = 59): #amount of time between humidifier runs (minutes, minutes)
    GPIO.output(Fan_GPIO, GPIO.HIGH)
    time.sleep(float(duration)*60)
    GPIO.output(Fan_GPIO, GPIO.LOW)
    time.sleep(float(interval)*60)

try:
    if cs.feature_toggles["fan_pid"] == "1":
        actuate_pid(float(sys.argv[1])) #trigger appropriate response
        GPIO.cleanup()
    else:
        actuate_interval(str(sys.argv[1]), str(sys.argv[2]))
        GPIO.cleanup() #this uses the timer instead
except:
    print("Interrupted")
    GPIO.cleanup()
