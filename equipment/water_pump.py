#---------------------------------------------------------------------------------------
#Manages Hardware and timer for watering
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

#import libraries
import RPi.GPIO as GPIO
import time
import json

from utils import concurrent_state as cs

cs.load_state()

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
water_GPIO = cs.hardware_config["equipment_gpio_map"]["water_relay"] #heater pin pulls from config file
GPIO.setup(water_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(water_GPIO, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function making PID discrete & actuate element accordingly
def actuate_pid(water_ctrl):
    if (water_ctrl >= 0) and (water_ctrl < 1):
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(1)

    if (water_ctrl >= 1) and (water_ctrl < 10):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(5) 
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 10) and (water_ctrl < 20):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(10)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 20) and (water_ctrl < 30):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(15)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 30) and (water_ctrl < 40):
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(20)
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(60)

    if (water_ctrl >= 40) and (water_ctrl < 50):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(25)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 50) and (water_ctrl < 60):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(30)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 60) and (water_ctrl < 70):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(35)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 70) and (water_ctrl < 80):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(40)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 80) and (water_ctrl < 85):
        GPIO.output(water_GPIO, GPIO.HIGH)
        time.sleep(45)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 85) and (water_ctrl < 90):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(50)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 90) and (water_ctrl < 95):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(55)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

    if (water_ctrl >= 95) and (water_ctrl <= 100):
        GPIO.output(water_GPIO,GPIO.HIGH)
        time.sleep(60)
        GPIO.output(water_GPIO,GPIO.LOW)
        time.sleep(60)

#define a function to actuate element
def actuate_interval(duration = 30, interval = 24): #amount of time between waterings (seconds, hours)
    GPIO.output(water_GPIO, GPIO.HIGH)
    time.sleep(float(duration))
    GPIO.output(water_GPIO, GPIO.LOW)
    time.sleep(float(interval)*float(3600))

try:
    if cs.feature_toggles["water_pid"] == "1":
        actuate_pid(float(sys.argv[1])) #trigger appropriate response
        GPIO.cleanup()
    else:
        actuate_interval(str(sys.argv[1]), str(sys.argv[2]))
        GPIO.cleanup() #this uses the timer instead
except:
    print("Interrupted")
    GPIO.cleanup()

