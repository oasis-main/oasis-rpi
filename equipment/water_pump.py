#---------------------------------------------------------------------------------------
# I/O for controlling a watering pump
#---------------------------------------------------------------------------------------
#import OS modules
import sys
import signal

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#import libraries
import rusty_pins
from peripherals import relays
from utils import concurrent_state as cs
from utils import error_handler as err

resource_name = "water_pump"

cs.load_state()
water_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["water_relay"]) #bcm pin_no pulls from config file
pin = rusty_pins.GpioOut(water_GPIO)

def clean_up(*args):
    cs.safety.unlock(cs.lock_filepath, resource_name)
    pin.set_low()
    sys.exit()

if __name__ == "__main__":
    cs.check_lock(resource_name)
    signal.signal(signal.SIGTERM, clean_up)
    try:
        if cs.structs["feature_toggles"]["water_pid"] == "1":
            print("Running water pump in pulse mode with " + sys.argv[1] + "%" + " power...")
            relays.actuate_slow_pwm(pin, intensity = float(sys.argv[1])) #trigger appropriate response
        else:
            print("Running water pump for " + sys.argv[1] + " second(s) every " + sys.argv[2] + " day(s)...")
            relays.actuate_interval_sleep(pin, duration = float(sys.argv[1]), sleep = float(sys.argv[2]), duration_units="seconds", sleep_units="days")
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception:
        print("Encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()


