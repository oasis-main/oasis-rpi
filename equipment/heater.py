#---------------------------------------------------------------------------------------
#Manages Hardware for Heating
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

resource_name = "heater"
cs.check_lock(resource_name)

#get hardware config
cs.load_state()
heat_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["heat_relay"]) #heater pin pulls from config file
pin = rusty_pins.GpioOut(heat_GPIO)

def clean_up(*args):
    print("Shutting down heater...")
    cs.safety.unlock(cs.lock_filepath, resource_name)
    relays.turn_off(pin)
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, clean_up)
    try:
        while True:
            if cs.structs["feature_toggles"]["heat_pid"] == "1":
                print("Heating in pulse mode with " + cs.structs["control_params"]["heat_feedback"] + "%" + " power...")
                relays.actuate_slow_pwm(pin, float(cs.structs["control_params"]["heat_feedback"])) #trigger appropriate response
            else:
                print("Heater on for " + cs.structs["control_params"]["heater_duration"] + " minute(s), off for " + cs.structs["control_params"]["heater_interval"] + " minute(s)...")
                relays.actuate_interval_sleep(pin, float(cs.structs["control_params"]["heater_duration"]), float(cs.structs["control_params"]["heater_interval"]), duration_units= "minutes", sleep_units="minutes")
   
            cs.load_state()
    except KeyboardInterrupt:
        print("Heater was interrupted.")
    except Exception:    
        print("Heater encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()
