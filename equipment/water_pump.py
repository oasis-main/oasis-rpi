#---------------------------------------------------------------------------------------
#Manages Hardware and timer for watering
#---------------------------------------------------------------------------------------
#import shell modules
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#import libraries
import time

from peripherals import relays
from utils import concurrent_state as cs

cs.load_state()

water_GPIO = cs.structs["hardware_config"]["equipment_gpio_map"]["water_relay"] #bcm pin_no pulls from config file
water_GPIO = int(water_GPIO)

if __name__ == "__main__":
    try:
        if cs.structs["feature_toggles"]["water_pid"] == "1":
            relays.actuate_slow_pwm(pin = water_GPIO, intensity = float(sys.argv[1])) #trigger appropriate response
        else:
            relays.actuate_interval_sleep(pin = water_GPIO, duration = float(sys.argv[1]), sleep = float(sys.argv[2]))
    except KeyboardInterrupt:
        print("Interrupted")
    except:
        print("Please provide the module water pump with operating parameters when calling.")


