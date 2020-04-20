import sys
import RPi.GPIO as GPIO
import time
import json

GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
Hum_GPIO = 3 #humidifier is going to be triggered with pin 3
GPIO.setup(Hum_GPIO, GPIO.OUT) #GPIO setup
GPIO.output(Hum_GPIO, GPIO.HIGH) #relay open = GPIO.HIGH, closed = GPIO.LOW

#define a function making PID discrete & actuate element accordingly
def actuate(humCtrl):
	if (humCtrl >= 0) and (humCtrl < 1):
		print("level 0")
		GPIO.output(Hum_GPIO, GPIO.HIGH) #off
		time.sleep(5)

	if (humCtrl >= 1) and (humCtrl < 10):
		print("level 1")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.9) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.1) #on

	if (humCtrl >= 10) and (humCtrl < 20):
		print("level 2")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.8) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.2) #on

	if (humCtrl >= 20) and (humCtrl < 30):
		print("level 3")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.7) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.3) #on

	if (humCtrl >= 30) and (humCtrl < 40):
		print("level 4")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.6) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.4) #on

	if (humCtrl >= 40) and (humCtrl < 50):
		print("level 5")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.5) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.5) #on

	if (humCtrl >= 50) and (humCtrl < 60):
		print("level 6")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.4) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.6) #on

	if (humCtrl >= 60) and (humCtrl < 70):
		print("level 7")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.3) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.7) #on

	if (humCtrl >= 70) and (humCtrl < 80):
		print("level 8")
                GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4.2) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(.8) #on

	if (humCtrl >= 80) and (humCtrl < 90):
		print("level 9")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
		time.sleep(4.1) #off
		GPIO.output(Hum_GPIO, GPIO.LOW)
		time.sleep(.9) #on

	if (humCtrl >= 90) and (humCtrl <= 100):
		print("level 10")
		GPIO.output(Hum_GPIO, GPIO.HIGH)
                time.sleep(4) #off
                GPIO.output(Hum_GPIO, GPIO.LOW)
                time.sleep(1) #on

try:
	while 1:
		with open('pid_out.json') as pid_in: #read pid feedback from .json
  			pid_commands = json.load(pid_in)
		actuate(pid_commands["hum"]) #trigger appropriate response
except KeyboardInterrupt:
        print 'Interrupted'
	GPIO.cleanup()
