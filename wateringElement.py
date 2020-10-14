#---------------------------------------------------------------------------------------
#Manages Hardware and timer for watering
#---------------------------------------------------------------------------------------

#import libraries
import sys
import sys
import RPi.GPIO as GPIO
import time
import json

#get hardware config
with open('/home/pi/hardware_config.json') as f:
  hardware_config = json.load(f)

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
H2o_GPIO = hardware_config["actuatorGPIOmap"]["wateringElement"] #heater pin pulls from config file 
GPIO.setup(H2o_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(H2o_GPIO, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function to actuate element
def actuate(mode = "on",duration = 30, interval = 3600): #amoubnt of time between waterings

    if mode == "on":
        GPIO.output(H2o_GPIO, GPIO.HIGH)
        time.sleep(float(duration))
        GPIO.output(H2o_GPIO, GPIO.LOW)
        time.sleep(float(interval))
    else:
        GPIO.output(H2o_GPIO, GPIO.LOW)
        time.sleep(float(interval))

try:
    actuate(str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3]))
    GPIO.cleanup()
except KeyboardInterrupt:
    print("Interrupted")
    GPIO.cleanup()

