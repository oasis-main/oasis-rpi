import base64
import requests
from PIL import Image
import os, sys
import time

ip = '18.218.2.179'
port = 3000
while 1:
    image_path = '/home/pi/Desktop/output.jpg'
    os.system('raspistill -o output.jpg')
    time.sleep(5)


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


