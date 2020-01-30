import serial
import time
import subprocess


ser = serial.Serial('/dev/ttyACM0',9600)
line = 0

def condisionReport(hum, heat):
    #humidity
    if hum > 75:
        print('moist')
    elif hum <  25:
        print('dry')
    else:
        print('normal humidity')


    #heat
    if heat > 90:
        print('hot')
    elif heat < 50:
        print('cold')
    else:
        print('normal temp') 

def listen():

    global line,ser

    if(ser.in_waiting > 0):
    print('----')        
        sensorInfo = str.strip(ser.readline()).split(' ')
    if len(sensorInfo)<2:
        pass
    else:
        print(sensorInfo)
        hum =float( sensorInfo[0])
        heat = float(sensorInfo[1])
            condisionReport(hum, heat)
    
        
        ser.reset_input_buffer()

while __name__ == "__main__":
    listen()
