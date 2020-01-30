import serial
import time
import subprocess


ser = serial.Serial('/dev/ttyACM0',9600)
line = 0


def main():
    while 1:
        listen()

def show_image1():
    print('show image 1')
    #subprocess.call('bash display_image.sh haveanawesomeday.jpg', shell=True)

def listen():
    global line,ser
    if(ser.in_waiting > 0):
        line = str.strip(ser.readline())
        print(line)
        if(line == '1'):
            show_image1()
        
        ser.reset_input_buffer()

main()