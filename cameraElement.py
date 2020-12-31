#---------------------------------------------------------------------------------------
#Manages Camera Timing & Image transmission
#TODO:
# - generalize IP, pass in as argumen from main file and take as input function to
# - functionalize image capture and posting capability

import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/grow-ctrl')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

#import libraries
import time
import base64
from PIL import Image
from subprocess import Popen
import requests
import json

#get device_state
with open('/home/pi/device_state.json') as d:
    device_state = json.load(d)
d.close()

with open('/home/pi/access_config.json', "r+") as a:
  access_config = json.load(a)
  id_token = access_config['id_token']
  local_id = access_config['local_id']
  refresh_token = access_config['refresh_token']
a.close()

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
	storage.child(user['userId']+'/'+path).put(path, user['idToken'])

#define a function to actuate element
def actuate(interval): #amount of time between shots

    #timestamp image
    timestamp = time.time()

    #add USB path

    #set timestamp file name
    image_path = '/home/pi/Pictures/culture_image'+str(timestamp)+'.jpg'

    still = Popen('sudo raspistill -o ' + str(image_path), shell=True) #snap: call the camera
    still.wait()

    #if image_path != '':
    #    with open(image_path, 'rb') as imageFile:
    #        image_data = base64.b64encode(imageFile.read()) #encode in base64 for sending
    #else:
    #    print('fail')
    #    image_data = 'custom_image'

    #data = json.dumps({"image": str(image_data)})

    if device_state["connected"] == "1":
        user, db, storage = initialize_user(refresh_token)
        send_image(user, storage, image_path)

    time.sleep(float(interval))

try:
    actuate(str(sys.argv[1]))
except KeyboardInterrupt:
    print("Interrupted")

