#---------------------------------------------------------------------------------------
#Manages Hardware for Heating
#---------------------------------------------------------------------------------------

#import shell modules
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import RPi.GPIO as GPIO
import time
from utils import concurrent_state as cs

#get hardware config
cs.load_state()

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Heat_GPIO = cs.structs["hardware_config"]["equipment_gpio_map"]["heat_relay"] #heater pin pulls from config file
GPIO.setup(Heat_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(Heat_GPIO, GPIO.LOW)

#define a function making PID discrete & actuate element accordingly
def actuate_pid(temp_ctrl = 50):
    if (temp_ctrl >= 0) and (temp_ctrl < 1):
        #print("level 0")
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(5)

    if (temp_ctrl >= 1) and (temp_ctrl < 10):
        #print("level 1")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(1) #on for 1
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 10) and (temp_ctrl < 20):
        #print("level 2")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(2) #on for 2
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 20) and (temp_ctrl < 30):
        #print("level 3")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(3) #on for 3
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 30) and (temp_ctrl < 40):
        #print("level 4")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(4) #on for 4
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 40) and (temp_ctrl < 50):
        #print("level 5")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(5) #on for 5
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 50) and (temp_ctrl < 60):
        #print("level 6")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(6) #on for 6
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 60) and (temp_ctrl < 70):
        #print("level 7")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(7) #on for 7
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 70) and (temp_ctrl < 80):
        #print("level 8")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(8) #on for 8
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 80) and (temp_ctrl < 90):
        #print("level 9")
        GPIO.output(Heat_GPIO, GPIO.HIGH)
        time.sleep(9) #on for 9
        GPIO.output(Heat_GPIO,GPIO.LOW)
        time.sleep(1) #off for 1

    if (temp_ctrl >= 90) and (temp_ctrl <= 100):
        #print("level 10")
        GPIO.output(Heat_GPIO,GPIO.HIGH)
        time.sleep(10) #on for 10

def actuate_interval(duration = 15, interval = 45): #amount of time between waterings (seconds, seconds)
    GPIO.output(Heat_GPIO, GPIO.HIGH)
    time.sleep(float(duration))
    GPIO.output(Heat_GPIO, GPIO.LOW)
    time.sleep(float(interval))

try:
    if cs.structs["feature_toggles"]["heat_pid"] == "1":
        actuate_pid(float(sys.argv[1])) #trigger appropriate response
    else:
        actuate_interval(float(sys.argv[1]),float(sys.argv[2])) #this uses the timer instead
except KeyboardInterrupt:
    print("Interrupted")
finally:
    GPIO.cleanup()
