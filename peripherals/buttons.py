import sys

#peripherals
import RPi.GPIO as GPIO

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

from utils import concurrent_state as cs

#declare UI variables
start_stop_button = None #holds GPIO object for starting and stopping core process
connect_internet_button = None #holds GPIO object for connecting device to internet
action_button = None #holds GPIO object for triggering the desired action

#setup buttons for the main program interface
def setup_button_interface(hardware_config): #depends on: , 'RPi.GPIO'; modifies: start_stop_button, connect_internet_button, run_action_button, state variables
    global start_stop_button, connect_internet_button, action_button
    
    print("Setting up button interface...")

    #specify gpio pin number mode
    GPIO.setmode(GPIO.BCM)

    #set button pins
    start_stop_button = int(cs.structs["hardware_config"]["button_gpio_map"]["start_stop_button"])
    connect_internet_button = int(cs.structs["hardware_config"]["button_gpio_map"]["connect_internet_button"])
    action_button = int(cs.structs["hardware_config"]["button_gpio_map"]["action_button"])

    #Setup buttons
    GPIO.setup(start_stop_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(connect_internet_button,GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(action_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#gets the state of a button (returns 1 if not pressed, 0 if pressed)
def get_button_state(button): #Depends on: RPi.GPIO; Modifies: None
    state = GPIO.input(button)
    return state

if __name__ == "__main__":
    print("This is a unit test for buttons.")
    import time
    cs.load_state()
    setup_button_interface(cs.structs["hardware_config"])
    if get_button_state(connect_internet_button) == 1:
        print("Button was initialized!")
    print("Ok, now press the button and hold it there for 5 seconds.")
    time.sleep(5)
    if get_button_state(connect_internet_button) == 0:
        print("Button press detected!")
    