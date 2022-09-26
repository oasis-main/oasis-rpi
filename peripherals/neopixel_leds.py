#must be run as root
#import shell modules
import sys
import os

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import board
import neopixel
import time

from utils import slow_concurrent_state as slow_cs

#get hardware config & device state
slow_cs.load_state()
num_leds = slow_cs.structs["hardware_config"]["onboard_led_config"]["num_leds"]
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

if __name__ == "__main__":
    run()


    