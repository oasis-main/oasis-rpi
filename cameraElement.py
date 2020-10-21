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
import requests
import json

id_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjBlM2FlZWUyYjVjMDhjMGMyODFhNGZmN2RjMmRmOGIyMzgyOGQ1YzYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vb2FzaXMtMTc1N2YiLCJhdWQiOiJvYXNpcy0xNzU3ZiIsImF1dGhfdGltZSI6MTYwMzIyMTc1OCwidXNlcl9pZCI6IjZ0ZHlqSjZ5RmtjaWo0VDdmS2hnbTZRRDBOcTIiLCJzdWIiOiI2dGR5ako2eUZrY2lqNFQ3ZktoZ202UUQwTnEyIiwiaWF0IjoxNjAzMjk2NDk4LCJleHAiOjE2MDMzMDAwOTgsImVtYWlsIjoiYXNkZkBhc2RmLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJhc2RmQGFzZGYuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoicGFzc3dvcmQifX0.Lr6DTPdN0Oaq8zqLVIFDJSh4UfQyVR_dbwYJZUGugIdDvt6tG-z5lLIGP-KYexhqGKLfcMReZNDGncu8T9uJvtoX4DuIb1kYlzszdZ-g74V99EkWY2HyQ26FYpWbp8aC3jUhKINO9koh13f4B47hsu_YtLCKg-Hazf3n4tuYjs26t_z_IxiX8Lslso_3qcMu3Rn5Rjl1cDo3ihQU7uTq8dtibfyD3NCLZtd9wIl_AgMViyDC13sKa79Gkz5TSKNPqzWsNNw8IBBzr61DcX1FEOSbteJD1sSXatUefrAeNwxdVG5yXgZX_rv7wY0rx9RkMbksmz7ycdYQPFfhW-PBpg"
local_id = "6tdyjJ6yFkcij4T7fKhgm6QD0Nq2"

#define a function to actuate element
def actuate(interval = 3600): #amoubnt of time between shots

    image_path = '/home/pi/Desktop/output.jpg'

    still = Popen('sudo raspistill -o ~/Desktop/output.jpg', stdout = None, shell = True) #snap: call the camera
    still.wait()

    if image_path != '':
        with open(image_path, 'rb') as imageFile:
            image_data = base64.b64encode(imageFile.read()) #encode in base64 for sending
    else:
        print('fail')
        image_data = 'custom_image'

    data = json.dumps({"image": str(image_data)})
    url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
    result = requests.patch(url,data)
    print(result)

    time.sleep(float(interval))

try:
    actuate(str(sys.argv[1]))
except KeyboardInterrupt:
    print("Interrupted")

