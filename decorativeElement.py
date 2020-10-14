#---------------------------------------------------------------------------------------
#Manages Hardware for Neopixel display
#---------------------------------------------------------------------------------------

#import libraries
import time
import datetime
import sys
import board
import neopixel

pixels = neopixel.NeoPixel(board.D21, 60)

#define a function to actuate element
def actuate(lightingMode, timeOn = 0, timeOff = 0, interval = 900): #time on must be less than time off

    now = datetime.datetime.now()
    HoD = now.hour

    if lightingMode == "off":
        pixels.fill((0, 255, 0)) #no circle
        time.sleep(interval)

    if lightingMode == "on":
        if timeOn < timeOff:
            if HoD >= timeOn and HoD < timeOff:
                pixels.fill((0, 255, 0)) #circle
                time.sleep(interval)
            if HoD < timeOn or HoD >= timeOff:
                pixels.fill((0, 0, 0)) #no circle
                time.sleep(interval)
        if timeOn > timeOff:
            if HoD >=  timeOn or HoD < timeOff:
                pixels.fill((0, 255, 0)) #circle
                time.sleep(interval)
            if HoD < timeOn and  HoD >= timeOff:
                pixels.fill((0, 0, 0)) #no circle
                time.sleep(interval)
        if timeOn == timeOff:
            pixels.fill((0, 255, 0)) #circle
            time.sleep(interval)

try:
    actuate(str(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
except KeyboardInterrupt:
    print("Interrupted")

