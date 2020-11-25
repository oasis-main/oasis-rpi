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
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT
import requests
import json

#get device_state
with open('/home/pi/device_state.json') as d:
    device_state = json.load(d)
d.close()

#define a function to actuate element
def actuate(interval = 3600): #amoubnt of time between shots

    image_path = '/home/pi/Desktop/output.jpg'

    still = Popen('sudo raspistill -o ~/Desktop/output.jpg', shell=True) #snap: call the camera
    still.wait()

    if image_path != '':
        with open(image_path, 'rb') as imageFile:
            image_data = base64.b64encode(imageFile.read()) #encode in base64 for sending
    else:
        print('fail')
        image_data = 'custom_image'

    data = json.dumps({"image": str(image_data)})

    if device_state["connected"] == "1":
        url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
        result = requests.patch(url,data)

    time.sleep(float(interval))

try:
    actuate(str(sys.argv[1]))
except KeyboardInterrupt:
    print("Interrupted")

