#---------------------------------------------------------------------------------------
#Manages Hardware for Humidity
#TODO:
#	(possible) define one function to handle various behavior
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
Hum_GPIO = cs.hardware_config["equipment_gpio_map"]["dehumidifier_relay"] #heater pin pulls from config file
GPIO.setup(Hum_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(Hum_GPIO, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function making PID discrete & actuate element accordingly
def actuate_pid(hum_ctrl):
    if (hum_ctrl >= 0) and (hum_ctrl < 1):
        #print("level 0")
        GPIO.output(Hum_GPIO, GPIO.LOW) #off
        time.sleep(20)

    if (hum_ctrl >= 1) and (hum_ctrl < 10):
        #print("level 1")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(2) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(18) #off

    if (hum_ctrl >= 10) and (hum_ctrl < 20):
        #print("level 2")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(4) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(16) #off

    if (hum_ctrl >= 20) and (hum_ctrl < 30):
        #print("level 3")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(6) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(16) #off

    if (hum_ctrl >= 30) and (hum_ctrl < 40):
        #print("level 4")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(8) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(12) #off

    if (hum_ctrl >= 40) and (hum_ctrl < 50):
        #print("level 5")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(10) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(10) #off

    if (hum_ctrl >= 50) and (hum_ctrl < 60):
        #print("level 6")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(12) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(8) #off

    if (hum_ctrl >= 60) and (hum_ctrl < 70):
        #print("level 7")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(14) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(6) #off

    if (hum_ctrl >= 70) and (hum_ctrl < 80):
        #print("level 8")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(16) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(4) #off

    if (hum_ctrl >= 80) and (hum_ctrl < 90):
        #print("level 9")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(18) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(2) #off

    if (hum_ctrl >= 90) and (hum_ctrl <= 100):
        #print("level 10")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(20) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(0) #off

def actuate_interval(duration = 15, interval = 45): #amount of time between humidifier runs (seconds, seconds)
    GPIO.output(Hum_GPIO, GPIO.HIGH)
    time.sleep(float(duration))
    GPIO.output(Hum_GPIO, GPIO.LOW)
    time.sleep(float(interval))

try:
    if cs.feature_toggles["hum_pid"] == "1":
        actuate_pid(float(sys.argv[1])) #trigger appropriate response
        GPIO.cleanup()
    else:
        actuate_interval(str(sys.argv[1]),str(sys.argv[2]))
        GPIO.cleanup() #this uses the timer instead
except:
    print("Interrupted")
    GPIO.cleanup()
