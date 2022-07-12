
import cv2
import numpy as np
from imaging import fastiecm

#move color intensity 
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

#take the raw file from 
def convert_picture(in_path, out_path):
    #create and configure camera object 
    original = cv2.imread(in_path) # load image
    image = np.array(original, dtype=float)/float(255) #convert to an array

    contrasted = contrast_stretch(image) #apply contrast to the image
    #cv2.imwrite('/home/pi/oasis-grow/data_out/contrasted.png', contrasted) #save contrasted image
    
    ndvi = calc_ndvi(contrasted) #calculate image ndvi
    #cv2.imwrite('/home/pi/oasis-grow/data_out/ndvi.png', ndvi) #save ndvi image
    
    color_mapped_prep = ndvi.astype(np.float) #prep colour mapping
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm.fastiecm) #apply colour mapping
    #display(color_mapped_image, "NDVI Preview")

    cv2.imwrite(out_path, color_mapped_image) #save cm'd image


if __name__ == "main":
    print("No main program here. Sorry! Look at the file to see importable functions.")


