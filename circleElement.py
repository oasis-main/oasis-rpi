#---------------------------------------------------------------------------------------
#Manages Hardware for Neopixel display
#---------------------------------------------------------------------------------------

#import libraries
import RPi.GPIO as GPIO
import time
import datetime
import sys

#hardware setup
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
circle_GPIO = 16 #light is going to be triggered with pin 17
GPIO.setup(circle_GPIO, GPIO.OUT) #GPIO setup relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function to actuate element
def actuate(lightingMode, timeOn = 0, timeOff = 0, interval = 900): #time on must be less than time off

    now = datetime.datetime.now()
    HoD = now.hour

    if lightingMode == "off":
        #no cirle
        time.sleep(interval)

    if lightingMode == "on":
        if timeOn < timeOff:
            if HoD >= timeOn and HoD < timeOff:
                #circle
                time.sleep(interval)
            if HoD < timeOn or HoD >= timeOff:
                #no circle
                time.sleep(interval)
        if timeOn > timeOff:
            if HoD >=  timeOn or HoD < timeOff:
                #circle
                time.sleep(interval)
            if HoD < timeOn and  HoD >= timeOff:
                #no circle
                time.sleep(interval)
        if timeOn == timeOff:
            #circle
            time.sleep(interval)

try:
    actuate(str(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    GPIO.cleanup()
except KeyboardInterrupt:
    print("Interrupted")
    GPIO.cleanup()

