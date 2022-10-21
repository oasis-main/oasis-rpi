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
cs.check_lock(resource_name)

#setup GPIO
cs.load_state()
fan_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["fan_relay"]) #fan pin pulls from config file
pin = rusty_pins.GpioOut(fan_GPIO)

def clean_up(*args):
    print("Shutting down fans...")
    cs.safety.unlock(cs.lock_filepath, resource_name)
    relays.turn_off(pin)
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, clean_up)
    try:
        while True:
            if cs.structs["feature_toggles"]["fan_pid"] == "1":
                print("Ventilating in pulse mode with " + cs.structs["control_params"]["fan_pid"] + "%" + " power...")
                relays.actuate_slow_pwm(pin, float(cs.structs["control_params"]["fan_pid"]), wattage=cs.structs["hardware_config"]["equipment_wattage"]["fan"], log="fan_kwh") #trigger appropriate response
            else:
                print("Fans on for " + cs.structs["control_params"]["fan_duration"] + " minute(s), off for " + cs.structs["control_params"]["fan_interval"] + " minute(s)...")
                relays.actuate_interval_sleep(pin, float(cs.structs["control_params"]["fan_duration"]), float(cs.structs["control_params"]["fan_interval"]), duration_units= "minutes", sleep_units="minutes", wattage=cs.structs["hardware_config"]["equipment_wattage"]["fan"], log="fan_kwh")
   
            cs.load_state()
    except KeyboardInterrupt:
        print("Fan was interrupted.")
    except Exception:    
        print("Fan encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()
        
