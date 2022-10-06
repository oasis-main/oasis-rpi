#add latching, normally-closed, and normally-open
#add multi-channel output results

import time
import datetime
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import rusty_pins

def turn_on(output, mode = "momentary"):
    if mode == "momentary":
        pass
    if mode == "latching":
        pass

def turn_off(output, mode = "momentary"):
    if mode == "momentary":
        pass
    if mode == "latching":
        pass

def actuate_time_hod(pin: int, time_on = 0, time_off = 0, interval = 20, units = "seconds"): #updates every 20 minutes by default 
    try:
        output = rusty_pins.GpioOut(pin)
        
        if units == "seconds":
            time_active = interval
        if units == "minutes":
            time_active = interval*60
        if units == "hours":
            time_active = interval*60**2
        if units == "days":
            time_active = interval*24*60**2

        now = datetime.datetime.now()
        HoD = now.hour

        if time_on < time_off:
            if HoD >= time_on and HoD < time_off:
                output.set_high() #light on (relay closed)
                time.sleep(float(time_active))
            if HoD < time_on or HoD >= time_off:
                output.set_low()
                time.sleep(float(time_active))
        if time_on > time_off:
            if HoD >=  time_on or HoD < time_off:
                output.set_high() #light on (relay closed)
                time.sleep(float(time_active))
            if HoD < time_on and  HoD >= time_off:
                output.set_low() #light on (relay closed)
                time.sleep(float(time_active))
        if time_on == time_off:
            output.set_high()
            time.sleep(float(interval)*60)
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        output.set_low()

def actuate_interval_sleep(pin: int, duration = 15, sleep = 45, units = "seconds"):
    try:
        output = rusty_pins.GpioOut(pin)
        
        if units == "seconds":
            time_active = duration
            time_sleep = sleep
        if units == "minutes":
            time_active = duration * 60
            time_sleep = sleep * 60
        if units == "hours":
            time_active = duration * 60 ** 2
            time_sleep = sleep * 60 ** 2
        if units == "days":
            time_active = duration * 24 * 60 ** 2
            time_sleep = sleep * 24 * 60 ** 2

        output.set_high()
        time.sleep(float(time_active)) #set seconds to minutes
        output.set_low()
        time.sleep(float(time_sleep))
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        output.set_low()

def actuate_slow_pwm(pin: int, intensity: int, pulse_domain = 10.0):
    try:
        output = rusty_pins.GpioOut(pin)

        if (intensity >= 0) and (intensity < 1):
            #print("level 0")
            output.set_low() #off
            time.sleep(pulse_domain)

        if (intensity >= 1) and (intensity < 10):
            #print("level 1")
            output.set_high()
            time.sleep(pulse_domain*(.1)) #on
            output.set_low()
            time.sleep(pulse_domain*(.9)) #off

        if (intensity >= 10) and (intensity < 20):
            #print("level 2")
            output.set_high()
            time.sleep(pulse_domain*(.2)) #on
            output.set_low()
            time.sleep(pulse_domain*(.8)) #off

        if (intensity >= 20) and (intensity < 30):
            #print("level 3")
            output.set_high()
            time.sleep(pulse_domain*(.3)) #on
            output.set_low()
            time.sleep(pulse_domain*(.7)) #off

        if (intensity >= 30) and (intensity < 40):
            #print("level 4")
            output.set_high()
            time.sleep(pulse_domain*(.4)) #on
            output.set_low()
            time.sleep(pulse_domain*(.6)) #off

        if (intensity >= 40) and (intensity < 50):
            #print("level 5")
            output.set_high()
            time.sleep(pulse_domain*(.5)) #on
            output.set_low()
            time.sleep(pulse_domain*(.5)) #off

        if (intensity >= 50) and (intensity < 60):
            #print("level 6")
            output.set_high()
            time.sleep(pulse_domain*(.6)) #on
            output.set_low()
            time.sleep(pulse_domain*(.4)) #off

        if (intensity >= 60) and (intensity < 70):
            #print("level 7")
            output.set_high()
            time.sleep(pulse_domain*(.7)) #on
            output.set_low()
            time.sleep(pulse_domain*(.3)) #off

        if (intensity >= 70) and (intensity < 80):
            #print("level 8")
            output.set_high()
            time.sleep(pulse_domain*(.8)) #on
            output.set_low()
            time.sleep(pulse_domain*(.2)) #off

        if (intensity >= 80) and (intensity < 90):
            #print("level 9")
            output.set_high()
            time.sleep(pulse_domain*(.9)) #on
            output.set_low()
            time.sleep(pulse_domain*(.1)) #off

        if (intensity >= 90) and (intensity <= 100):
            #print("level 10")
            output.set_high()
            time.sleep(pulse_domain) #on
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        output.set_low()

if __name__ == "__main__":
    print("This is a unit test for relays physical I/O.")
    print("Watch the lights...")
    actuate_time_hod(pin = 14, interval=.5)
    actuate_interval_sleep(pin = 14, duration = 15, sleep = 45)