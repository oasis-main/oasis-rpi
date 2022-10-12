#OS libraries
import sys

#Time libraries
import time
import datetime

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#import rusty_pins and initialize GPIO pin from calling process
#pass in the rust pin object for scoping & resource management

def turn_on(output, switch_mode = "momentary", normal_state = "open", pulse_width = 1):
    if switch_mode == "momentary":
        if normal_state == "open":
            output.set_high()
        if normal_state == "closed":
            output.set_low()
    if switch_mode == "latching": #this is going to be the same whether our switch is NO or NC
        output.set_high() #assumes the latch itself is NO
        time.sleep(pulse_width)
        output.set_low()

def turn_off(output, switch_mode = "momentary", normal_state = "open", pulse_width = 1):
    if switch_mode == "momentary":
        if normal_state == "open":
            output.set_low()
        if normal_state == "closed":
            output.set_high()
    if switch_mode == "latching":
        output.set_high()
        time.sleep(pulse_width)
        output.set_low()

def actuate_time_hod(output, time_on = 0, time_off = 0, interval = 20, interval_units = "minutes"): #updates every 20 minutes by default 
    try:
        if interval_units == "seconds":
            time_active = interval
        if interval_units == "minutes":
            time_active = interval*60
        if interval_units == "hours":
            time_active = interval*60**2
        if interval_units == "days":
            time_active = interval*24*60**2

        now = datetime.datetime.now()
        HoD = now.hour

        if time_on < time_off:
            if HoD >= time_on and HoD < time_off:
                turn_on(output) #light on (relay closed)
                time.sleep(float(time_active))
            if HoD < time_on or HoD >= time_off:
                turn_off(output)
                time.sleep(float(time_active))
        if time_on > time_off:
            if HoD >=  time_on or HoD < time_off:
                turn_on(output) #light on (relay closed)
                time.sleep(float(time_active))
            if HoD < time_on and  HoD >= time_off:
                turn_off(output) #light on (relay closed)
                time.sleep(float(time_active))
        if time_on == time_off:
            turn_on(output)
            time.sleep(float(interval)*60)
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        turn_off(output)

def actuate_interval_sleep(output, duration = 15, sleep = 45, duration_units = "seconds", sleep_units = "seconds"):
    try:
        if duration_units == "seconds":
            time_active = duration
        if duration_units == "minutes":
            time_active = duration * 60
        if duration_units == "hours":
            time_active = duration * 60 ** 2
        if duration_units == "days":
            time_active = duration * 24 * 60 ** 2

        if sleep_units == "seconds":
            time_sleep = sleep
        if sleep_units == "minutes":
            time_sleep = sleep * 60
        if sleep_units == "hours":
            time_sleep = sleep * 60 ** 2
        if sleep_units == "days":
            time_sleep = sleep * 24 * 60 ** 2

        turn_on(output)
        time.sleep(float(time_active)) #set seconds to minutes
        turn_off(output)
        time.sleep(float(time_sleep))
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        turn_off(output)

def actuate_slow_pwm(output, intensity: int, pulse_domain = 10.0):
    try:
        if (intensity >= 0) and (intensity < 1):
            #print("level 0")
            turn_off(output) #off
            time.sleep(pulse_domain)

        if (intensity >= 1) and (intensity < 10):
            #print("level 1")
            turn_on(output)
            time.sleep(pulse_domain*(.1)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.9)) #off

        if (intensity >= 10) and (intensity < 20):
            #print("level 2")
            turn_on(output)
            time.sleep(pulse_domain*(.2)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.8)) #off

        if (intensity >= 20) and (intensity < 30):
            #print("level 3")
            turn_on(output)
            time.sleep(pulse_domain*(.3)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.7)) #off

        if (intensity >= 30) and (intensity < 40):
            #print("level 4")
            turn_on(output)
            time.sleep(pulse_domain*(.4)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.6)) #off

        if (intensity >= 40) and (intensity < 50):
            #print("level 5")
            turn_on(output)
            time.sleep(pulse_domain*(.5)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.5)) #off

        if (intensity >= 50) and (intensity < 60):
            #print("level 6")
            turn_on(output)
            time.sleep(pulse_domain*(.6)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.4)) #off

        if (intensity >= 60) and (intensity < 70):
            #print("level 7")
            turn_on(output)
            time.sleep(pulse_domain*(.7)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.3)) #off

        if (intensity >= 70) and (intensity < 80):
            #print("level 8")
            turn_on(output)
            time.sleep(pulse_domain*(.8)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.2)) #off

        if (intensity >= 80) and (intensity < 90):
            #print("level 9")
            turn_on(output)
            time.sleep(pulse_domain*(.9)) #on
            turn_off(output)
            time.sleep(pulse_domain*(.1)) #off

        if (intensity >= 90) and (intensity <= 100):
            #print("level 10")
            turn_on(output)
            time.sleep(pulse_domain) #on
    except KeyboardInterrupt:
        print("You terminated the program while a relay was in use. Cleaning up...")
    finally:
        turn_off(output)

if __name__ == "__main__":
    print("This is a unit test for relays physical I/O.")
    print("Watch the lights...")
    actuate_time_hod(pin = 14, interval=5)
    actuate_interval_sleep(pin = 14, duration = 5, sleep = 5)
    actuate_time_hod(pin = 14, interval=5)