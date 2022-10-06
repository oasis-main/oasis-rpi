#add latching, normally-closed, and normally-open
#add multi-channel output results

import time
import datetime

import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import rusty_pins

def actuate_time(pin: int, time_on = 0, time_off = 0, interval = 900):
    try:
        output = rusty_pins.GpioOut(pin)
        
        now = datetime.datetime.now()
        HoD = now.hour

        if time_on < time_off:
            if HoD >= time_on and HoD < time_off:
                output.set_high() #light on (relay closed)
                time.sleep(float(interval)*60)
            if HoD < time_on or HoD >= time_off:
                output.set_low()
                time.sleep(float(interval)*60)
        if time_on > time_off:
            if HoD >=  time_on or HoD < time_off:
                output.set_high() #light on (relay closed)
                time.sleep(float(interval)*60)
            if HoD < time_on and  HoD >= time_off:
                output.set_low() #light on (relay closed)
                time.sleep(float(interval)*60)
        if time_on == time_off:
            output.set_high()
            time.sleep(float(interval)*60)
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        output.set_low()

def interval_actuate(pin: int, duration = 15, interval = 45):
    try:
        output = rusty_pins.GpioOut(pin)
        
        output.set_high()
        time.sleep(float(duration))
        output.set_low()
        time.sleep(float(interval))
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        output.set_low()

def slow_pwm_actuate(pin: int, intensity: int, pulse_domain = 10.0):
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