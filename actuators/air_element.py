#---------------------------------------------------------------------------------------
#Manages Hardware for Lighting
#TODO:
# - generalize IP, pass in as argumen from main file and take as input function to
# - functionalize image capture and posting capability
# - adjust light timing to allow for and type of window
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
import datetime
import json

from utils import concurrent_state as cs

cs.load_state()

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Air_GPIO = cs.hardware_config["actuator_gpio_map"]["air_relay"] #heater pin pulls from config file
GPIO.setup(Air_GPIO, GPIO.OUT) #GPIO setup relay open = GPIO.HIGH, closed = GPIO.LOW
GPIO.output(Air_GPIO, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function to actuate element
def actuate(time_on = 0, time_off = 0, interval = 900): #time on must be less than time off

    now = datetime.datetime.now()
    HoD = now.hour


    if time_on < time_off:
        if HoD >= time_on and HoD < time_off:
            GPIO.output(Air_GPIO, GPIO.HIGH) #light on (relay closed)
            time.sleep(interval)
        if HoD < time_on or HoD >= time_off:
            GPIO.output(Air_GPIO, GPIO.LOW)
            time.sleep(interval)
    if time_on > time_off:
        if HoD >=  time_on or HoD < time_off:
            GPIO.output(Air_GPIO, GPIO.HIGH) #light on (relay closed)
            time.sleep(interval)
        if HoD < time_on and  HoD >= time_off:
            GPIO.output(Air_GPIO, GPIO.LOW) #light on (relay closed)
            time.sleep(interval)
    if time_on == time_off:
        GPIO.output(Air_GPIO, GPIO.HIGH)
        time.sleep(interval)

try:
    actuate(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    GPIO.cleanup()
except KeyboardInterrupt:
    print("Interrupted")
    GPIO.cleanup()

