#---------------------------------------------------------------------------------------
#Manages Hardware for Humidity 
#TODO:
# - generalize IP, pass in as argumen from main file and take as input function to
# - functionalize image capture and posting capability
# - adjust light timing to allow for and type of window
#---------------------------------------------------------------------------------------

#import libraries
import sys
import time
import base64
from PIL import Image
import os
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT
from firebase import firebase
import pyrebase


config = {
    "apiKey": "AIzaSyDdL5DdIc9M--RAJ_qd6exJ8hy4irSxP_8",
    "authDomain": "oasis-test-8acee.firebaseapp.com",
    "databaseURL": "https://oasis-test-8acee.firebaseio.com/",
    "storageBucket": "oasis-test-8acee.appspot.com"
}

firebase = pyrebase.initialize_app(config)

storage = firebase.storage()

#define a function to actuate element
def actuate(interval = 3600): #amoubnt of time between shots

    image_path = '/home/pi/Desktop/output.jpg'

    still = Popen('sudo raspistill -o ~/Desktop/output.jpg', stdout = None, shell = True) #snap: call the camera
    still.wait()

    storage.child("images/lastpic.jpg").put(image_path)

    time.sleep(float(interval))

try:
    actuate(str(sys.argv[1]))
except KeyboardInterrupt:
    print("Interrupted")

