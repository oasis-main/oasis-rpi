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
with open('/home/pi/hardware_config.json') as f:
  hardware_config = json.load(f)

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Hum_GPIO = hardware_config["actuatorGPIOmap"]["humidityElement"] #heater pin pulls from config file 
GPIO.setup(Hum_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(Hum_GPIO, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function making PID discrete & actuate element accordingly
def actuate(humCtrl):
    if (humCtrl >= 0) and (humCtrl < 1):
        print("level 0")
        GPIO.output(Hum_GPIO, GPIO.LOW) #off
        time.sleep(20)

    if (humCtrl >= 1) and (humCtrl < 10):
        print("level 1")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(2) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(18) #off

    if (humCtrl >= 10) and (humCtrl < 20):
        print("level 2")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(4) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(16) #off


    if (humCtrl >= 20) and (humCtrl < 30):
        print("level 3")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(6) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(16) #off

    if (humCtrl >= 30) and (humCtrl < 40):
        print("level 4")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(8) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(12) #off

    if (humCtrl >= 40) and (humCtrl < 50):
        print("level 5")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(10) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(10) #off

    if (humCtrl >= 50) and (humCtrl < 60):
        print("level 6")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(12) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(8) #off

    if (humCtrl >= 60) and (humCtrl < 70):
        print("level 7")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(14) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(6) #off

    if (humCtrl >= 70) and (humCtrl < 80):
        print("level 8")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(16) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(4) #off

    if (humCtrl >= 80) and (humCtrl < 90):
        print("level 9")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(18) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(2) #off

    if (humCtrl >= 90) and (humCtrl <= 100):
        print("level 10")
        GPIO.output(Hum_GPIO, GPIO.HIGH)
        time.sleep(20) #on
        GPIO.output(Hum_GPIO, GPIO.LOW)
        time.sleep(0) #off

try:
    actuate(float(sys.argv[1]))
    GPIO.cleanup()
except KeyboardInterrupt:
    print("Interrupted")
    GPIO.cleanup()
