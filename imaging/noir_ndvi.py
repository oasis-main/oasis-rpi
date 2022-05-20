
import cv2
import numpy as np
from imaging import fastiecm
from picamera import PiCamera
import picamera.array

#create and capture stream object
def capture_stream(cam):
    stream = picamera.array.PiRGBArray(cam)
    cam.capture(stream, format='bgr', use_video_port=True)
    original = stream.array
    return original

def display(image, image_name):
    image = np.array(image, dtype=float)/float(255)
    shape = image.shape
    height = int(shape[0] / 2)
    width = int(shape[1] / 2)
    image = cv2.resize(image, (width, height))
    cv2.namedWindow(image_name)
    cv2.imshow(image_name, image)
    cv2.waitKey(0)
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
    bottom[bottom==0] = 0.01
    ndvi = (r.astype(float) - b) / bottom # THIS IS THE CHANGED LINE
    return ndvi

def take_picture():
    #create and configure camera object 
    cam = PiCamera()
    cam.rotation = 180
    cam.resolution = (1920, 1080) # Uncomment if using a Pi Noir camera
    #cam.resolution = (2592, 1952) # Comment this line if using a Pi Noir camera

    original = capture_stream(cam)#create and capture stream object
    #display(original, 'Original')
    contrasted = contrast_stretch(original)
    #display(contrasted, 'Contrasted original')
    cv2.imwrite('/home/pi/oasis-grow/data_out/contrasted.png', contrasted)
    ndvi = calc_ndvi(contrasted)
    #display(ndvi, 'NDVI')
    cv2.imwrite('/home/pi/oasis-grow/data_out/ndvi.png', ndvi)
    ndvi_contrasted = contrast_stretch(ndvi)
    #display(ndvi_contrasted, 'NDVI Contrasted')
    cv2.imwrite('/home/pi/oasis-grow/data_out/ndvi_contrasted.png', ndvi_contrasted)
    color_mapped_prep = ndvi_contrasted.astype(np.uint8)
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm.fastiecm)
    #display(color_mapped_image, 'Color mapped')
    cv2.imwrite('/home/pi/oasis-grow/data_out/color_mapped_image.png', color_mapped_image)


if __name__ == "main":
    #create and configure camera object 
    cam = PiCamera()
    cam.rotation = 180
    cam.resolution = (1920, 1080) # Uncomment if using a Pi Noir camera
    #cam.resolution = (2592, 1952) # Comment this line if using a Pi Noir camer
    
    #create and capture stream object
    original = capture_stream()
    display(original, 'Original')
    
    #apply contrast
    contrasted = contrast_stretch(original)
    display(contrasted, 'Contrasted original')
    cv2.imwrite('/home/pi/oasis-grow/data_out/contrasted.png', contrasted)
    
    #calculate ndvi from contrast
    ndvi = calc_ndvi(contrasted)
    display(ndvi, 'NDVI')
    cv2.imwrite('/home/pi/oasis-grow/data_out/ndvi.png', ndvi)
    
    #apply contrast to ndvi
    ndvi_contrasted = contrast_stretch(ndvi)
    display(ndvi_contrasted, 'NDVI Contrasted')
    cv2.imwrite('/home/pi/oasis-grow/data_out/ndvi_contrasted.png', ndvi_contrasted)
    
    #convert ndvi into a color-mapped version 
    color_mapped_prep = ndvi_contrasted.astype(np.uint8)
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm.fastiecm)
    display(color_mapped_image, 'Color mapped')
    cv2.imwrite('/home/pi/oasis-grow/data_out/color_mapped_image.png', color_mapped_image)


