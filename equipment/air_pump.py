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

resource_name = "air_pump"
cs.check_lock(resource_name)

#setup GPIO
cs.load_state()
air_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["air_relay"]) #air pump pin pulls from config file
pin = rusty_pins.GpioOut(air_GPIO)

running = True

def clean_up(*args):
    print("Shutting down air pump...")
    global running
    running = False
    relays.turn_off(pin)
    cs.safety.unlock(cs.lock_filepath, resource_name)
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM,clean_up)
    try:
        while running:
            print("Turning air pump on at " + cs.structs["control_params"]["time_start_air"] + ":00 and off at " + cs.structs["control_params"]["time_stop_air"] + ":00, refreshing every " + cs.structs["control_params"]["air_interval"] + " minutes...")
            relays.actuate_time_hod(pin, int(cs.structs["control_params"]["time_start_air"]), int(cs.structs["control_params"]["time_stop_air"]), int(cs.structs["control_params"]["air_interval"]), interval_units = "minutes", wattage=cs.structs["hardware_config"]["equipment_wattage"]["air_pump"], log="air_pump_kwh")
    except KeyboardInterrupt:
        print("Air pump was interrupted")
    except Exception:
        print("Air pump ncountered an error!")
        print(err.full_stack())
    finally:
        clean_up()


