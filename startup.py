from __future__ import print_function
import RPi.GPIO as GPIO
import time
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT

GPIO.setmode(GPIO.BCM)

GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Button to GPIO23

running = False
try:
    while True:
        button_state = GPIO.input(23)
        if button_state == False:
            if running == False:
                print('starting...')
                running = True
                sensingfeedback = Popen(['python', 'sensingfeedback_v1.4.py'], stdout=PIPE, stdin=PIPE, stderr=PIPE) #start python subprocess
                time.sleep(3.5)
            else:
                print('stopping...')
                running = False
                sensingfeedback.kill()
                sensingfeedback.wait()
                time.sleep(3.5)
except:
    GPIO.cleanup()
    print('Exited.')
