#---------------------------------------------------------------------------------------
# Hardware for controlling a watering pump
#---------------------------------------------------------------------------------------
#import OS modules
import sys
import signal
import time

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
water_GPIO = int(cs.structs["hardware_config"]["equipment_gpio_map"]["water_relay"]) #bcm pin # pulls from config file
pin = rusty_pins.GpioOut(water_GPIO)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, cs.wrapped_sys_exit)
    try:
        while True:
            if cs.structs["feature_toggles"]["water_pid"] == "1":
                print("Running water pump in pulse mode with " + cs.structs["control_params"]["moisture_feedback"] + "%" + " power...")
                relays.actuate_slow_pwm(pin, intensity = float(cs.structs["control_params"]["moisture_feedback"]), wattage=cs.structs["hardware_config"]["equipment_wattage"]["water_pump"], log="water_pump_kwh") #trigger appropriate response
            else:
                print("Running water pump for " + cs.structs["control_params"]["watering_duration"] + " second(s) every " + cs.structs["control_params"]["watering_interval"] + " day(s)...")
                relays.actuate_interval_sleep(pin, duration = float(cs.structs["control_params"]["watering_duration"]), sleep = float(cs.structs["control_params"]["watering_interval"]), duration_units="seconds", sleep_units="days", wattage=cs.structs["hardware_config"]["equipment_wattage"]["water_pump"], log="water_pump_kwh")
            cs.load_state()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Water pump was interrupted")
    except Exception:
        print("Water pump encountered an error!")
        print(err.full_stack())
    finally:
        print("Shutting down water pump...")
        try:
            relays.turn_off(pin)
        except:
            print(resource_name + " has no relay objects remaining.")
        
        cs.rusty_pipes.unlock(cs.lock_filepath, resource_name)


