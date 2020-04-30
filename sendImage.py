import base64
import requests
from PIL import Image
import os, sys

ip = '18.218.2.179'
port = 3000

image_path = '/home/pi/Desktop/output.jpg'

if image_path != '':
    with open(image_path, 'rb') as imageFile:
        image_data = base64.b64encode(imageFile.read())
else:
    print('fail')
    image_data = 'cusdom_image'

json={'image':image_data}
#print(image_data)
requests.post('http://'+ip+':'+str(port)+'/upload/image', json)
print('sent')

