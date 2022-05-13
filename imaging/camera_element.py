#---------------------------------------------------------------------------------------
#Manages Camera Timing & Image transmission

import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/home/pi/oasis-grow/imaging')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

#import libraries
import time
import base64
import PIL
from PIL import Image
from subprocess import Popen
import requests
import json
import pyrebase
import noir_ndvi
from utils import concurrent_state as cs

def initialize_user(refresh_token):
#app configuration information
    config = {"apiKey": "AIzaSyD-szNCnHbvC176y5K6haapY1J7or8XtKc",
              "authDomain": "oasis-1757f.firebaseapp.com",
              "databaseURL": "https://oasis-1757f.firebaseio.com/",
              "storageBucket": "oasis-1757f.appspot.com"
             }

    firebase = pyrebase.initialize_app(config)
    auth = firebase.auth()
    db = firebase.database()
    user = auth.refresh(refresh_token)
    storage = firebase.storage()

    return user, db, storage

def send_image(user, storage, path):
    #send new image to firebase
    storage.child(user['userId'] + "/" + cs.access_config["device_name"] + "/image.jpg").put(path, user['idToken'])
    print("sent image")

    #tell firebase that there is a new image
    cs.patch_firebase("new_image","1")
    print("firebase has an image in waiting")

def take_picture(image_path):
    #take picture and save to standard location
    still = Popen(["raspistill", "-awb", "auto", "-o", str(image_path)]) #snap: call the camera
    still.wait()

def take_picture_NDVI(image_path):
    noir_ndvi.take_picture()
    still = Popen(["cp", "/home/pi/oasis-grow/data_out/color_mapped_image.png", str(image_path)]) #snap: call the camera
    still.wait()

def save_to_feed(image_path):
    #timestamp image
    timestamp = time.time()
    #move timestamped image into feed
    save_most_recent = Popen(["cp", str(image_path), "/home/pi/oasis-grow/data_out/image_feed/culture_image" + str(timestamp)+'.jpg'])
    save_most_recent.wait()

#define a function to actuate element
def actuate(interval): #amount of time between shots in minutes
    cs.load_state()
    
    if cs.feature_toggles["ndvi"] == "1":
        take_picture_NDVI('/home/pi/oasis-grow/data_out/image.jpg')
    else:
        take_picture('/home/pi/oasis-grow/data_out/image.jpg')

    if cs.feature_toggles["save_images"] == "1":
        save_to_feed('/home/pi/oasis-grow/data_out/image.jpg')

    if cs.device_state["connected"] == "1":

        #get user info
        user, db, storage = initialize_user(cs.access_config["refresh_token"])
        print("got credentials")

        #send new image to firebase
        send_image(user, storage, '/home/pi/oasis-grow/data_out/image.jpg')

    time.sleep(float(interval)*60)

if __name__ == '__main__':
    try:
        actuate(str(sys.argv[1]))
    except KeyboardInterrupt:
        print("Interrupted")

