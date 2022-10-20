#---------------------------------------------------------------------------------------
# Hardware for controlling a watering pump
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
cs.check_lock(resource_name)

cs.load_state()
water_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["water_relay"]) #bcm pin_no pulls from config file
pin = rusty_pins.GpioOut(water_GPIO)

def clean_up(*args):
    print("Shutting down water pump...")
    cs.safety.unlock(cs.lock_filepath, resource_name)
    relays.turn_off(pin)
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, clean_up)
    try:
        while True:
            if cs.structs["feature_toggles"]["water_pid"] == "1":
                print("Running water pump in pulse mode with " + cs.structs["control_params"]["moisture_feedback"] + "%" + " power...")
                relays.actuate_slow_pwm(pin, intensity = float(cs.structs["control_params"]["moisture_feedback"])) #trigger appropriate response
            else:
                print("Running water pump for " + sys.argv[1] + " second(s) every " + sys.argv[2] + " day(s)...")
                relays.actuate_interval_sleep(pin, duration = float(cs.structs["control_params"]["watering_duration"]), sleep = float(cs.structs["control_params"]["watering_interval"]), duration_units="seconds", sleep_units="days")
    
            cs.load_state()
    except KeyboardInterrupt:
        print("Water pump was interrupted")
    except Exception:
        print("Water pump encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()


