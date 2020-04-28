import RPi.GPIO as GPIO   # Import the GPIO library.
import time               # Import time library

GPIO.setmode(GPIO.BCM)    #.BOARD to use pin number when referencing GPIO pins.
                          # Can use GPIO.setmode(GPIO.BCM) instead to use
                          # Broadcom SOC channel names.

GPIO.setup(12, GPIO.OUT)  # Set GPIO pin 12 to output mode.

pwm = GPIO.PWM(12, 100)   # Initialize PWM on pwmPin 100Hz frequency
dc=0                               # set dc variable to 0 for 0%
pwm.start(dc)                      # Start PWM with 0% duty cycle

def set(level = 0): #set duty cycle (power level 0-100)
	pwm.ChangeDutyCycle(level)

def cleanup():
	set(0)
	pwm.stop()
	GPIO.cleanup()
