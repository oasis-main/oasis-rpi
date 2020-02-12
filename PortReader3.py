import serial
import time
import subprocess
import PID
import os.path
#######
def readConfig ():
    global targetT
    with open ('/tmp/pid.conf', 'r') as f:
        config = f.readline().split(',')
        pid.SetPoint = float(config[0])
        targetT = pid.SetPoint
        pid.setKp (float(config[1]))
        pid.setKi (float(config[2]))
        pid.setKd (float(config[3]))

def createConfig ():
    if not os.path.isfile('/tmp/pid.conf'):
        with open ('/tmp/pid.conf', 'w') as f:
            f.write('%s,%s,%s,%s'%(targetT,P,I,D))



#######

####
#arduino
####
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

    ##
    #DHT
    ##
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
        

    ##
    #PID
    ##
    readConfig()
    #read temperature data
    a0 = adc.read_voltage(0)
    temperature = (a0 - 0.5) * 100

    pid.update(temperature)
    targetPwm = pid.output
    targetPwm = max(min( int(targetPwm), 100 ),0)

    print "Target: %.1f C | Current: %.1f C | PWM: %s %%"%(targetT, temperature, targetPwm)

    # Set PWM expansion channel 0 to the target setting
    pwmExp.setupDriver(0, targetPwm, 0)
    time.sleep(0.5)


while __name__ == "__main__":

    ###
    #PID
    ###
    pwmExp.setVerbosity(-1)
    pwmExp.driverInit()
    adc = AdcExp.AdcExp()

    targetT = 35
    P = 10
    I = 1
    D = 1

    pid = PID.PID(P, I, D)
    pid.SetPoint = targetT
    pid.setSampleTime(1)
    
    createConfig()
    listen()

