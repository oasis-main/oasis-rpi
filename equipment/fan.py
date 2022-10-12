#---------------------------------------------------------------------------------------
#Manages Hardware for Fans / Ventilation
#---------------------------------------------------------------------------------------

#import shell modules
import sys
import signal

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import rusty_pins
from peripherals import relays
from utils import concurrent_state as cs
from utils import error_handler as err

resource_name = "fan"

#setup GPIO
cs.load_state()
fan_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["fan_relay"]) #heater pin pulls from config file
pin = rusty_pins.GpioOut(fan_GPIO)

def clean_up(*args):
    cs.safety.unlock(cs.lock_filepath, resource_name)
    pin.set_low()
    sys.exit()

if __name__ == '__main__':
    cs.check_lock(resource_name)
    signal.signal(signal.SIGTERM, clean_up)
    try:
        if cs.structs["feature_toggles"]["fan_pid"] == "1":
            print("Ventilating in pulse mode with " + sys.argv[1] + "%" + " power...")
            relays.actuate_slow_pwm(pin, float(sys.argv[1])) #trigger appropriate response
        else:
            print("Fans on for " + sys.argv[1] + " minute(s), off for " + sys.argv[2] + " minute(s)...")
            relays.actuate_interval_sleep(pin, float(sys.argv[1]), float(sys.argv[2]), duration_units= "minutes", sleep_units="minutes")
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception:    
        print("Encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()
        
