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

#get hardware config
with open('/home/pi/hardware_config.json') as h:
  hardware_config = json.load(h)

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
H2o_GPIO = hardware_config["actuator_gpio_map"]["watering_relay"] #heater pin pulls from config file
GPIO.setup(H2o_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(H2o_GPIO, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function to actuate element
def actuate(duration = 30, interval = 24): #amoubnt of time between waterings

    GPIO.output(H2o_GPIO, GPIO.HIGH)
    time.sleep(float(duration))
    GPIO.output(H2o_GPIO, GPIO.LOW)
    time.sleep(float(interval)*3600)

try:
    actuate(str(sys.argv[1]),str(sys.argv[2])))
    GPIO.cleanup()
except KeyboardInterrupt:
    print("Interrupted")
    GPIO.cleanup()

