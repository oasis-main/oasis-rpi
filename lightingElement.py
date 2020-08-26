#---------------------------------------------------------------------------------------
#Manages Hardware for Lighting
#TODO:
# - generalize IP, pass in as argumen from main file and take as input function to
# - functionalize image capture and posting capability
# - adjust light timing to allow for and type of window
#---------------------------------------------------------------------------------------

#import libraries
import RPi.GPIO as GPIO
import time
import datetime
import sys

#hardware setup
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Light_GPIO = 17 #light is going to be triggered with pin 17
GPIO.setup(Light_GPIO, GPIO.OUT) #GPIO setup relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function to actuate element
def actuate(lightingMode, timeOn = 0, timeOff = 0, interval = 900): #time on must be less than time off

    now = datetime.datetime.now()
    HoD = now.hour

    if lightingMode == "off":
        GPIO.output(Light_GPIO, GPIO.LOW) #light off (relay open)
        time.sleep(interval)

    if lightingMode == "on":
        if timeOn < timeOff:
            if HoD >= timeOn and HoD < timeOff:
                GPIO.output(Light_GPIO, GPIO.HIGH) #light on (relay closed)
                time.sleep(interval)
            if HoD < timeOn or HoD >= timeOff:
                GPIO.output(Light_GPIO, GPIO.LOW)
                time.sleep(interval)
        if timeOn > timeOff:
            if HoD >=  timeOn or HoD < timeOff:
                GPIO.output(Light_GPIO, GPIO.HIGH) #light on (relay closed)
                time.sleep(interval)
            if HoD < timeOn and  HoD >= timeOff:
                GPIO.output(Light_GPIO, GPIO.LOW) #light on (relay closed)
                time.sleep(interval)
        if timeOn == timeOff:
            GPIO.output(Light_GPIO, GPIO.HIGH)
            time.sleep(interval)

try:
    actuate(str(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    GPIO.cleanup()
except KeyboardInterrupt:
    print("Interrupted")
    GPIO.cleanup()

