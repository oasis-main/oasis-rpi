import base64
import requests
from PIL import Image
import os, sys
import time
import subprocess32
from subprocess32 import Popen, PIPE, STDOUT

def snapSend():
	ip = '54.172.134.78'
	port = 3000
	image_path = '/home/pi/Desktop/output.jpg' #set pathways

	still = Popen('sudo raspistill -o ~/Desktop/output.jpg', stdout = None, shell = True) #snap: call the camera
	still.wait()

	if image_path != '':
    		with open(image_path, 'rb') as imageFile:
        		image_data = base64.b64encode(imageFile.read()) #encode in base64 for sending
	else:
    		print('fail')
    		image_data = 'custom_image'

	json={'image':image_data}
	#print(image_data)
	requests.post('http://'+ip+':'+str(port)+'/upload/image', json) #send: post to /upload/image endpoint


