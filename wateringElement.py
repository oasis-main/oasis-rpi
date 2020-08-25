#---------------------------------------------------------------------------------------
#Manages Hardware and timer for watering
#---------------------------------------------------------------------------------------

#import libraries
import sys
import sys
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
H2o_GPIO = 14 #humidifier is going to be triggered with pin 3
GPIO.setup(H2o_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(H2o_GPIO, GPIO.HIGH) #relay open = GPIO.HIGH, closed = GPIO.LOW


#define a function to actuate element
def actuate(duration = 30, interval = 3600): #amoubnt of time between waterings

GPIO.output(H2o_GPIO, GPIO.LOW)

time.sleep(float(duration))

GPIO.output(H2o_GPIO, GPIO.HIGH)

time.sleep(float(interval))

try:
    actuate(str(sys.argv[1]),str(sys.argv[2]))
except KeyboardInterrupt:
    print("Interrupted")

