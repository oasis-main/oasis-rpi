#---------------------------------------------------------------------------------------
#Manages Hardware for Lighting
#---------------------------------------------------------------------------------------

#import shell modules
import sys
import signal

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#import libraries
import time
import datetime

import rusty_pins
from peripherals import relays
from utils import concurrent_state as cs
from utils import error_handler as err

#get configs
cs.load_state()
light_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["light_relay"]) #heater pin pulls from config file
pin = rusty_pins.GpioOut(light_GPIO)

resource_name = "light"

def clean_up(*args):
    cs.safety.unlock(cs.lock_filepath, resource_name)
    pin.set_low()
    sys.exit()

if __name__ == '__main__':
    try:
        relays.actuate_time_hod(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        GPIO.cleanup()

