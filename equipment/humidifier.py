#---------------------------------------------------------------------------------------
#Manages Hardware for Humidity
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

resource_name = "humidifier"
cs.check_lock(resource_name)

#setup GPIO
cs.load_state()#get configs
hum_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["humidifier_relay"]) #heater pin pulls from config file
pin = rusty_pins.GpioOut(hum_GPIO)

def clean_up(*args):
    cs.safety.unlock(cs.lock_filepath, resource_name)
    pin.set_low()
    sys.exit()

'''Here's the old calling code:
if cs.locks[resource_name] == 0:
        if cs.structs["feature_toggles"]["hum_pid"] == "1":
            humidity_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/humidifier.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
        else:
            humidity_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/humidifier.py', cs.structs["control_params"]["humidifier_duration"], cs.structs["control_params"]["humidifier_interval"]])
'''

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, clean_up)
    try:
        if cs.structs["feature_toggles"]["hum_pid"] == "1":
            print("Running humidifier in pulse mode with " + sys.argv[1] + "%" + " power...")
            relays.actuate_slow_pwm(pin, float(sys.argv[1])) #trigger appropriate response
        else:
            print("Running humidifier for " + sys.argv[1] + " minute(s) on, " + sys.argv[2] + " minute(s) off...")
            relays.actuate_interval_sleep(pin, float(sys.argv[1]), float(sys.argv[2]), duration_units= "minutes", sleep_units="minutes")
    except KeyboardInterrupt:
        print("Humidifier was interrupted.")
    except Exception:    
        print("Humidifier ncountered an error!")
        print(err.full_stack())
    finally:
        clean_up()