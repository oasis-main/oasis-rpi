#---------------------------------------------------------------------------------------
#Manages Hardware for Lighting
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

resource_name = "lights"
cs.check_lock(resource_name)

#get configs
cs.load_state()
light_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["light_relay"]) #heater pin pulls from config file
pin = rusty_pins.GpioOut(light_GPIO)

def clean_up(*args):
    print("Shutting down lights...")
    cs.safety.unlock(cs.lock_filepath, resource_name)
    relays.turn_off(pin)
    sys.exit()

'''This is the old calling code
light_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/lights.py', cs.structs["control_params"]["time_start_light"], cs.structs["control_params"]["time_stop_light"], cs.structs["control_params"]["lighting_interval"]]) #If running, then skips. If free then restarts.
'''

if __name__ == '__main__':
    signal.signal(signal.SIGTERM,clean_up)
    try:
        while True:
            print("Turning lights on at " + sys.argv[1] + ":00 and off at " + sys.argv[2] + ":00, refreshing every " + sys.argv[3] + " minutes...")
            pin = relays.actuate_time_hod(pin, int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), interval_units = "minutes")
    except KeyboardInterrupt:
        print("Lights were interrupted.")
    except Exception:
        print("Lights encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()

