#---------------------------------------------------------------------------------------
#Manages Hardware for Lighting
#---------------------------------------------------------------------------------------

#import shell modules
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#import libraries
import time
import datetime

import rusty_pins
from peripherals import relays
from utils import concurrent_state as cs
from utils import error_handler as err

cs.load_state()

#setup GPIO
GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Air_GPIO = cs.structs["hardware_config"]["equipment_gpio_map"]["air_relay"] #heater pin pulls from config file
GPIO.setup(Air_GPIO, GPIO.OUT) #GPIO setup relay open = GPIO.HIGH, closed = GPIO.LOW
GPIO.output(Air_GPIO, GPIO.LOW) #relay open = GPIO.HIGH, closed = GPIO.LOW

if __name__ == "__main__":
    try:
        actuate_hod(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    except KeyboardInterrupt:
        print("Interrupted")
    finally:    
        GPIO.cleanup()


