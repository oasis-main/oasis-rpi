
import cv2
import numpy as np
from imaging import fastiecm
from picamera import PiCamera
import picamera.array

#create and capture stream object
def capture_stream(cam):
    stream = picamera.array.PiRGBArray(cam)
    cam.capture(stream, format='bgr', use_video_port=True)
    raw = stream.array
    return raw

def display(image, image_name):
    image = np.array(image, dtype=float)/float(255)
    shape = image.shape
    height = int(shape[0] / 2)
    width = int(shape[1] / 2)
    image = cv2.resize(image, (width, height))
    cv2.namedWindow(image_name)
    cv2.imshow(image_name, image)
    cv2.waitKey(10000)
    cv2.destroyAllWindows()

def contrast_stretch(im):
    in_min = np.percentile(im, 5)
    in_max = np.percentile(im, 95)

    out_min = 0.0
    out_max = 255.0

    out = im - in_min
    out *= ((out_min - out_max) / (in_min - in_max))
    out += in_min

    return out

#calculate NDVI
def calc_ndvi(image):
    b, g, r = cv2.split(image)
    bottom = (r.astype(float) + b.astype(float))
    bottom[bottom==0] = 0.0001
    ndvi = (r.astype(float) - b) / bottom # THIS IS THE CHANGED LINE
    return ndvi

def take_picture():
    #create and configure camera object 
    cam = PiCamera()
    #cam.preview_fullscreen=True

    #cam.rotation = 180
    cam.resolution = (1920, 1080) # Uncomment if using a Pi Noir camera
    #cam.resolution = (2592, 1952) # Comment this line if using a Pi Noir camera
    
    raw = capture_stream(cam) #capture photo with no IR filter
    cam.close() #close camera object and return resources

    contrasted = contrast_stretch(raw) #apply contrast to the image
    #cv2.imwrite('/home/pi/oasis-grow/data_out/contrasted.png', contrasted) #save contrasted image
    
    ndvi = calc_ndvi(contrasted) #calculate image ndvi
    #cv2.imwrite('/home/pi/oasis-grow/data_out/ndvi.png', ndvi) #save ndvi image
    
    color_mapped_prep = ndvi.astype(np.uint8) #prep colour mapping
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm.fastiecm) #apply colour mapping
    #display(color_mapped_image, "NDVI Preview")

    cv2.imwrite('/home/pi/oasis-grow/data_out/color_mapped_image.png', color_mapped_image) #save cm'd image

if __name__ == "main":
    print("No main program here. Sorry! Look at the file to see importable functions.")


