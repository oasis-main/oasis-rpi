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
light_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["light_relay"]) #lights pin pulls from config file
pin = rusty_pins.GpioOut(light_GPIO)

running = True

def clean_up(*args):
    print("Shutting down lights...")
    global running
    running = False
    relays.turn_off(pin)
    cs.safety.unlock(cs.lock_filepath, resource_name)
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM,clean_up)
    try:
        while running:
            print("Turning lights on at " + cs.structs["control_params"]["time_start_light"] + ":00 and off at " + cs.structs["control_params"]["time_stop_light"] + ":00, refreshing every " + cs.structs["control_params"]["lighting_interval"] + " minutes...")
            pin = relays.actuate_time_hod(pin, int(cs.structs["control_params"]["time_start_light"]), int(cs.structs["control_params"]["time_stop_light"]), int(cs.structs["control_params"]["lighting_interval"]), interval_units = "minutes", wattage=cs.structs["hardware_config"]["equipment_wattage"]["lights"], log="lights_kwh")
    except KeyboardInterrupt:
        print("Lights were interrupted.")
    except Exception:
        print("Lights encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()

