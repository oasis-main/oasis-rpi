#---------------------------------------------------------------------------------------
#Manages Hardware for Fans / Ventilation
#---------------------------------------------------------------------------------------

#import shell modules
import sys
import signal

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import time

import rusty_pins
from utils import concurrent_state as cs
from utils import error_handler as err

#get hardware config
cs.load_state()

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Fan_GPIO = cs.structs["hardware_config"]["equipment_gpio_map"]["fan_relay"] #heater pin pulls from config file
GPIO.setup(Fan_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(Fan_GPIO, GPIO.LOW)

def clean_up(*args):
    cs.safety.unlock(cs.lock_filepath, resource_name)
    pin.set_low()
    sys.exit()

if __name__ == '__main__':
    try:
        if cs.structs["feature_toggles"]["fan_pid"] == "1":
            actuate_pid(float(sys.argv[1])) #trigger appropriate feedback response
        else:
            actuate_interval(float(sys.argv[1]), float(sys.argv[2])) #this uses the timer instead
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        GPIO.cleanup()
        
