import serial
import time
import subprocess


ser = serial.Serial('/dev/ttyACM0',9600)
line = 0

def listen():

    global line,ser

    if(ser.in_waiting > 0):
        
        line = str.strip(ser.readline())
        
        print(line)
        
        ser.reset_input_buffer()

while __name__ == "__main__":
    listen()