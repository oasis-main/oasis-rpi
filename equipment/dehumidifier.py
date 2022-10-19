#---------------------------------------------------------------------------------------
#Manages Hardware for Dehumidifier
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

resource_name = "dehumidifier"
cs.check_lock(resource_name)

#get hardware config
cs.load_state()
dehum_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["dehumidifier_relay"]) #heater pin pulls from config file
pin = rusty_pins.GpioOut(dehum_GPIO)

def clean_up(*args):
    print("Shutting down dehumidifier...")
    cs.safety.unlock(cs.lock_filepath, resource_name)
    relays.turn_off(pin)
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, clean_up)
    try:
        while True:
            if cs.structs["feature_toggles"]["dehum_pid"] == "1":
                print("Running dehumidifier in pulse mode with " + cs.structs["control_params"]["dehum_feedback"] + "%" + " power...")
                relays.actuate_slow_pwm(pin, float(cs.structs["control_params"]["dehum_feedback"])) #trigger appropriate response
            else:
                print("Running dehumidifier for " + sys.argv[1] + " minute(s) on, " + sys.argv[2] + " minute(s) off...")
                relays.actuate_interval_sleep(pin, float(cs.structs["control_params"]["dehumidifier_duration"]), float(cs.structs["control_params"]["dehumidifier_interval"]), duration_units= "minutes", sleep_units="minutes")
    
            cs.load_state()
    except KeyboardInterrupt:
        print("Dehumidifier was interrupted.")
    except Exception:    
        print("Dehumidifier encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()
