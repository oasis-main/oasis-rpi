#import shell modules
import sys
import signal

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import board
import neopixel
import time

from utils import slow_concurrent_state as slow_cs
from utils import error_handler as err

resource_name = "led"
slow_cs.check_lock(resource_name) #anything GPIO-touching should check the lock before the object is declared

#get hardware config & device state
slow_cs.load_state()
num_leds = int(slow_cs.structs["hardware_config"]["onboard_led_config"]["num_leds"])
pixels = neopixel.NeoPixel(board.D21, num_leds)

def check_led_status():
    slow_cs.load_state()
    if slow_cs.structs["device_state"]["led_status"] == "off":
        for x in range(0, num_leds):
            pixels[x] = (0, 0, 0)
        return

    #Connected, Running (green, looping)
    if slow_cs.structs["device_state"]["led_status"] == "connected_running":
        for x in range(0, num_leds):
            pixels[x] = (0, 10, 0)
            time.sleep(0.04)
        for x in range(0, num_leds):
            pixels[x] = (0, 5, 0)
            time.sleep(0.04)   
        return

    #Connected, Idle (green, still)
    if slow_cs.structs["device_state"]["led_status"] == "connected_idle":
        for x in range(0, num_leds):
            pixels[x] = (0, 5, 0)
            time.sleep(0.04)
        return

    #Offline, Running (white, looping)
    if slow_cs.structs["device_state"]["led_status"] == "offline_running":
        for x in range(0, num_leds):
            pixels[x] = (10, 10, 10)
            time.sleep(0.04)
        for x in range(0, num_leds):
            pixels[x] = (5, 5, 5)
            time.sleep(0.04)   
        return

    #Offline, Idle (white, still)
    if slow_cs.structs["device_state"]["led_status"] == "offline_idle":
        for x in range(0, num_leds):
            pixels[x] = (5, 5, 5)
            time.sleep(0.04)
        return

    #Master sends error message (red, still)
    if slow_cs.structs["device_state"]["led_status"] == "error":
        for x in range(0, num_leds):
            pixels[x] = (5, 0, 0)
            time.sleep(0.04)
        return

    #AP-mode, Server accepting connections (blue, looping)
    if slow_cs.structs["device_state"]["led_status"] == "accepting_wifi_connection":
        for x in range(0, num_leds):
            pixels[x] = (0, 0, 10)
            time.sleep(0.04)
        for x in range(0, num_leds):
            pixels[x] = (0, 0, 5)
            time.sleep(0.04)   
        return

def run():
    while True:
        check_led_status()

def clean_up(*args):
    slow_cs.unlock(slow_cs.lock_filepath, resource_name) #free the leds for system

    #off
    for x in range(0, num_leds): #kill the neopixels
        pixels[x] = (0, 0, 10)
        time.sleep(0.04)
    for x in range(0, num_leds):
        pixels[x] = (0, 0, 5)
        time.sleep(0.04)   
    
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM,clean_up)
    try:
        run()
    except KeyboardInterrupt:
        print("A user interrupted the program")
    except Exception:
        print("Encountered an error!")
        print(err.full_stack())
    finally:
        clean_up()