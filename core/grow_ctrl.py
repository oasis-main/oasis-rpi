#system
from multiprocessing.context import set_spawning_popen
import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

#Process management
import serial
import subprocess
from subprocess import Popen, PIPE, STDOUT
import signal
import gc
import traceback

#communicating with firebase
import requests

#data handling
import json
import csv

#dealing with specific times of the day
import time
import datetime

#import other oasis packages
import reset_model
import concurrent_state as cs

#declare process management variables
ser_in = None
heat_process = None
dehumidify_process= None
humidity_process = None
fan_process = None
light_process = None
camera_process = None
water_process = None
air_process = None

#declare sensor data variables
temperature = 0
last_temperature = 0
last_target_temperature = 0
error_cum_temperature = 0

humidity = 0
last_humidity = 0
last_target_humidity = 0
error_cum_humidity = 0

co2 = 0
last_co2 = 0
last_target_co2 = 0
error_cum_co2 = 0

soil_moisture = 0
last_soil_moisture = 0
last_target_soil_moisture = 0
error_cum_soil_moisture = 0

vpd = 0
water_low = 0
lux = 0
ph = 0

#declare timekeeping variables
data_timer = None

#write some data to a .csv, takes a dictionary and a path
def write_csv(filename, dict): #Depends on: 'pandas',
    file_exists = os.path.isfile(filename)

    with open (filename, 'a') as csvfile:
        headers = ["time", "temperature", "humidity", "water_low"]
        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        writer.writerow(dict)
    
    return 

#attempts connection to microcontroller
def start_serial(): #Depends on:'serial'; Modifies: ser_out
    global ser_in

    try:
        try:
            ser_in = serial.Serial("/dev/ttyUSB0", 9600)
            print("Started serial communication with Arduino Nano.")
        except:
            ser_in = serial.Serial("/dev/ttyACM0", 9600)
            print("Started serial communication with Arduino Uno.")
    except Exception as e:
        ser_in = None
        print("Serial connection not found")

#gets data from serial, will parse a simple string or accept a dictionary
def listen(): #Depends on 'serial', start_serial(); Modifies: ser_in, sensor_info, temperature, humidity, last_temperature, last_humidity, water_low
    #load in global vars
    global ser_in, temperature, humidity, last_temperature, last_humidity, water_low

    if ser_in == None:
        return

    try:
        #listen for data from aurdino, split it by space
        sensor_info = ser_in.readline().decode('UTF-8').strip().split(' ')
        
        #legacy sensor app: data is space-separated string
        last_humidity = humidity
        humidity =float(sensor_info[0])

        last_temperature = temperature
        temperature =float(sensor_info[1])

        water_low = int(sensor_info[2])
    except Exception as e:
        sensor_info = json.loads(str(ser_in.readline().decode('UTF-8').strip()))
        print(type(sensor_info))


#PD controller to modulate heater feedback
def heat_pd(temperature, target_temperature, last_temperature, last_target_temperature, P_heat, I_heat, D_heat): #no dependencies
    global error_cum_temperature

    err_temperature = target_temperature-temperature    #If target is 70 and temperature is 60, this value = 10, more heat
                                                        #If target is 50 and temperature is 60, this value is negative, less heat

    temperature_dot = temperature-last_temperature  #If temp is increasing, this value is positive (+#)
                                                    #If temp is decreasing, this value is negative (-#)

    err_cum_temperature = err_cum_temperature + err_temperature

    target_temperature_dot = target_temperature-last_target_temperature #When target remains the same, this value is 0
                                                                        #When adjusting target up, this value is positive (+#)
                                                                        #When adjusting target down, this value is negative (-#)

    err_dot_temperature = target_temperature_dot-temperature_dot    #When positive, boosts heat signal
                                                                    #When negative, dampens heat signal
    heat_level  = P_heat * err_temperature + D_heat * err_dot_temperature
    heat_level  = max(min(int(heat_level), 100), 0)

    return heat_level

#PD controller to modulate dehumidifier feedback
def dehum_pd(humidity, target_humidity, last_humidity, last_target_humidity, P_hum, D_hum): #no dependencies
    global error_cum_humidity

    err_humidity = humidity - target_humidity   #If target is 60 and humidity is 30, this value is negative, less dehum
                                                #If target is 30 and humidity is 60, this value = 30, more dehum
 
    humidity_dot = last_humidity - humidity #If hum increasing, this value is negative (-#)
                                            #If hum decreasing, this value is positive (+#)

    target_humidity_dot = last_target_humidity - target_humidity    #When target remains the same, this value is 0
                                                                    #When adjusting target down, this value is positive (+#)
                                                                    #When adjusting target up, this value is negative (-#)

    err_dot_humidity = humidity_dot - target_humidity_dot   #When positive, dampens dehum signal
                                                            #When negative, boosts duhum signal

    dehumidify_level  = P_hum * err_humidity + D_hum * (0 - err_dot_humidity)
    dehumidify_level  = max(min(int(dehumidify_level), 100), 0)

    return dehumidify_level

#PD controller to modulate humidifier feedback
def hum_pd(humidity, target_humidity, last_humidity, last_target_humidity, P_hum, D_hum): #no dependencies
    global error_cum_humidity
    
    err_humidity = target_humidity-humidity

    humidity_dot = humidity-last_humidity

    target_humidity_dot = target_humidity-last_target_humidity

    err_dot_humidity = target_humidity_dot-humidity_dot

    humidity_level  = P_hum*err_humidity + D_hum*err_dot_humidity
    humidity_level  = max(min(int(humidity_level),100),0)

    return humidity_level

#PD controller to modulate fan feedback
def fan_pd(temperature, humidity, target_temperature, target_humidity, last_temperature, last_humidity, last_target_temperature, last_target_humidity, Pt_fan, Ph_fan, Dt_fan, Dh_fan): #no dependencies
    global error_cum_temperature, error_cum_humidity, error_cum_co2
    
    err_temperature = temperature-target_temperature
    err_humidity = humidity-target_humidity

    temperature_dot = temperature-last_temperature
    humidity_dot = humidity-last_humidity

    target_temperature_dot = target_temperature-last_target_temperature
    target_humidity_dot = target_humidity-last_target_humidity

    err_dot_temperature = temperature_dot-target_temperature_dot
    err_dot_humidity = humidity_dot-target_humidity_dot

    fan_level  = Pt_fan*err_temperature + Ph_fan*err_humidity + Dt_fan*err_dot_temperature + Dh_fan*err_dot_humidity
    fan_level  = max(min(int(fan_level),100),0)

    return fan_level

#poll heat subprocess if applicable and relaunch/update actuators
def run_heat(intensity): #Depends on: 'subprocess'; Modifies: heat_process
    global heat_process

    try:
        poll_heat = heat_process.poll() #heat
        if poll_heat is not None:
            heat_process = Popen(['python3', '/home/pi/oasis-grow/actuators/heatingElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        heat_process = Popen(['python3', '/home/pi/oasis-grow/actuators/heatingElement.py', str(intensity)]) #If no process, then starts

#poll humidityf subprocess if applicable and relaunch/update actuators
def run_hum(intensity): #Depends on: 'subprocess'; Modifies: hum_process
    global humidity_process

    try:
        poll_humidity = humidity_process.poll() #humidity
        if poll_humidity is not None:
            humidity_process = Popen(['python3', '/home/pi/oasis-grow/actuators/humidityElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        humidity_process = Popen(['python3', '/home/pi/oasis-grow/actuators/humidityElement.py', str(intensity)]) #If no process, then starts

#poll dehumidify subprocess if applicable and relaunch/update actuators
def run_dehum(intensity): #Depends on: 'subprocess'; Modifies: hum_process
    global dehumidify_process

    try:
        poll_dehumidify = dehumidify_process.poll() #dehumidify
        if poll_dehumidify is not None:
            dehumidify_process = Popen(['python3', '/home/pi/oasis-grow/actuators/dehumidifyElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        dehumidify_process = Popen(['python3', '/home/pi/oasis-grow/actuators/dehumidifyElement.py', str(intensity)]) #If no process, then starts


#poll fan subprocess if applicable and relaunch/update actuators
def run_fan(intensity): #Depends on: 'subprocess'; Modifies: humidity_process
    global fan_process

    try:
        poll_fan = fan_process.poll() #fan
        if poll_fan is not None:
            fan_process = Popen(['python3', '/home/pi/oasis-grow/actuators/fanElement.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        fan_process = Popen(['python3', '/home/pi/oasis-grow/actuators/fanElement.py', str(intensity)]) #If no process, then starts

#poll light subprocess if applicable and relaunch/update actuators
def run_light(time_on, time_off, refresh_frequency):
    global light_process #Depends on: 'subprocess'; Modifies: light_process

    try:
        poll_light = light_process.poll() #light
        if poll_light is not None:
            light_process = Popen(['python3', '/home/pi/oasis-grow/actuators/lightingElement.py', str(time_on), str(time_off), str(refresh_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        light_process = Popen(['python3', '/home/pi/oasis-grow/actuators/lightingElement.py', str(time_on), str(time_off), str(refresh_frequency)]) #If no process, then starts

#poll camera subprocess if applicable and relaunch/update actuators
def run_camera(picture_frequency): #Depends on: 'subprocess'; Modifies: camera_process
    global camera_process

    try:
        poll_camera = camera_process.poll() #camera
        if poll_camera is not None:
            camera_process = Popen(['python3', '/home/pi/oasis-grow/imaging/cameraElement.py', str(picture_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        camera_process = Popen(['python3', '/home/pi/oasis-grow/imaging/cameraElement.py', str(picture_frequency)]) #If no process, then starts

#poll water subprocess if applicable and relaunch/update actuators
def run_water(watering_duration, watering_frequency): #Depends on: 'subprocess'; Modifies: water_process
    global water_process

    try:
        poll_water = water_process.poll() #water
        if poll_water is not None:
            water_process = Popen(['python3', '/home/pi/oasis-grow/actuators/wateringElement.py', str(watering_duration), str(watering_frequency)]) #If running, then skips. If idle then restarts, If no process, then fails
    except:
        water_process = Popen(['python3', '/home/pi/oasis-grow/actuators/wateringElement.py', str(watering_duration), str(watering_frequency)]) #If no process, then starts

#poll air subprocess if applicable and relaunch/update actuators
def run_air(time_on, time_off, refresh_frequency):
    global air_process #Depends on: 'subprocess'; Modifies: light_process

    try:
        poll_air = air_process.poll() #light
        if poll_air is not None:
            air_process = Popen(['python3', '/home/pi/oasis-grow/actuators/airElement.py', str(time_on), str(time_off), str(refresh_frequency)]) #If running, then skips. If idle then restarts, If no proce$
    except Exception as e:
        air_process = Popen(['python3', '/home/pi/oasis-grow/actuators/airElement.py', str(time_on), str(time_off), str(refresh_frequency)]) #If no process, then starts


def clean_up_processes():
    global heat_process, humidity_process, fan_process, light_process, camera_process, water_process, air_process        

    #clean up all processes
    cs.load_state()

    if (cs.feature_toggles["heater"] == "1") and (heat_process != None): #go through toggles and kill active processes
        heat_process.terminate()
        heat_process.wait()

    if (cs.feature_toggles["humidifier"] == "1") and (humidity_process != None):
        humidity_process.terminate()
        humidity_process.wait()

    if (cs.feature_toggles["fan"] == "1") and (fan_process != None):
        fan_process.terminate()
        fan_process.wait()

    if (cs.feature_toggles["light"] == "1") and (light_process != None):
        light_process.terminate()
        light_process.wait()

    if (cs.feature_toggles["camera"] == "1") and (camera_process != None):
        camera_process.terminate()
        camera_process.wait()

    if (cs.feature_toggles["water"] == "1") and (water_process != None):
        water_process.terminate()
        water_process.wait()

    if (cs.feature_toggles["air"] == "1") and (air_process != None):
        air_process.terminate()
        air_process.wait()

    gc.collect()

#terminates the program and all running subprocesses
def terminate_program(): #Depends on: cs.load_state(), 'sys', 'subprocess' #Modifies: heat_process, humidity_process, fan_process, light_process, camera_process, water_process

    print("Terminating Program...")
    clean_up_processes()

    #flip "running" to 0
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "0")

    sys.exit()

def main_setup():
    global data_timer

    #Load state variables to start the main program
    cs.load_state()

    #Exit early if opening subprocess daemon
    if str(sys.argv[1]) == "daemon":
        print("grow_ctrl daemon started")
        #kill the program
        sys.exit()
    if str(sys.argv[1]) == "main":
        print("grow_ctrl main started")
        #log main start
        #flip "running" to 1 to make usable from command line
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "1")
        #continue with program execution
        pass
    else:
        print("please offer valid run parameters")
        sys.exit()

    #attempt to make serial connection
    start_serial()

    #start the clock for timimg .csv writes and data exchanges with server
    data_timer = time.time()

def main_loop():
    global data_timer, last_target_temperature, last_target_humidity

    #launch main program loop
    try:
        print("------------------------------------------------------------")

        while True:

            last_target_temperature = int(cs.grow_params["target_temperature"]) #save last temperature and humidity targets to calculate delta for PD controllers
            last_target_humidity = int(cs.grow_params["target_humidity"])

            cs.load_state() #refresh the state variables to get new parameters


            if (cs.feature_toggles["temp_hum_sensor"] == "1") or (cs.feature_toggles["water_low_sensor"] == "1"):
                try: #attempt to read data from sensor, raise exception if there is a problem
                    listen() #this will be changed to run many sensor functions as opposed to one serial listener
                except Exception as e:
                    print(e)
                    print("Serial Port Failure")

            if cs.feature_toggles["heater"] == "1":
                print("Target Temperature: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(int(cs.grow_params["target_temperature"]),temperature, heat_pd(temperature,
                                                                                                                                  int(cs.grow_params["target_temperature"]),
                                                                                                                                  last_temperature,
                                                                                                                                  last_target_temperature,
                                                                                                                                  int(cs.grow_params["P_temp"]),
                                                                                                                                  int(cs.grow_params["D_temp"]))))
            if cs.feature_toggles["humidifier"] == "1":
                print("Target Humidity: %.1f %% | Current: %.1f %% | Hum_PID: %s %%"%(int(cs.grow_params["target_humidity"]), humidity, hum_pd(humidity,
                                                                                                                               int(cs.grow_params["target_humidity"]),
                                                                                                                               last_humidity,
                                                                                                                               last_target_humidity,
                                                                                                                               int(cs.grow_params["P_hum"]),
                                                                                                                               int(cs.grow_params["D_hum"]))))

            if cs.feature_toggles["fan"] == "1":
                print("Fan PD: %s %%"%(fan_pd(temperature,
                                              humidity,
                                              int(cs.grow_params["target_temperature"]),
                                              int(cs.grow_params["target_humidity"]),
                                              last_temperature,
                                              last_humidity,
                                              last_target_temperature,
                                              last_target_humidity,
                                              int(cs.grow_params["Pt_fan"]),
                                              int(cs.grow_params["Ph_fan"]),
                                              int(cs.grow_params["Dt_fan"]),
                                              int(cs.grow_params["Dh_fan"]))))

            if cs.feature_toggles["light"] == "1":
                print("Light Turns on at: %i :00 Local Time  | Turns off at: %i :00 Local Time"%(int(cs.grow_params["time_start_light"]), int(cs.grow_params["time_stop_light"])))

            if cs.feature_toggles["camera"] == "1":
                print("Image every %i minute(s)"%(int(cs.grow_params["camera_interval"])))

            if cs.feature_toggles["water"] == "1":
                print("Watering for: %i second(s) every: %i hour(s)"%(int(cs.grow_params["watering_duration"]), int(cs.grow_params["watering_interval"])))

            if cs.feature_toggles["water_low_sensor"] == "1":
                if water_low == 1:
                    print("Water Level Low!")

            print("------------------------------------------------------------")
            #write data and send to server after set time elapses
            if time.time() - data_timer > 300:

                try:

                    if cs.feature_toggles["save_data"] == "1":
                        #save data to .csv
                        print("Writing to csv")
                        write_csv('/home/pi/oasis-grow/data_out/sensor_feed/sensor_data.csv',{"time": [str(time.strftime('%l:%M%p %Z %b %d, %Y'))], "temperature": [str(temperature)], "humidity": [str(humidity)], "water_low": [str(water_low)]})

                    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "temperature", str(temperature))
                    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "humidity", str(humidity))
                    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "water_low", str(water_low))

                    data_timer = time.time()

                except Exception as e:
                    print(e)
                    data_timer = time.time()

            #update actuators in use
            if cs.feature_toggles["heater"] == "1":
                run_heat(str(heat_pd(temperature,int(cs.grow_params["target_temperature"]),last_temperature,last_target_temperature,int(cs.grow_params["P_temp"]),int(cs.grow_params["D_temp"]))))
            if cs.feature_toggles["humidifier"] == "1":
                run_hum(str(hum_pd(humidity,int(cs.grow_params["target_humidity"]),last_humidity,last_target_humidity,int(cs.grow_params["P_hum"]),int(cs.grow_params["D_hum"]))))
            if cs.feature_toggles["fan"] == "1":
                run_fan(fan_pd(temperature,humidity,int(cs.grow_params["target_temperature"]),int(cs.grow_params["target_humidity"]),last_temperature,last_humidity,last_target_temperature,last_target_humidity,int(cs.grow_params["Pt_fan"]),int(cs.grow_params["Ph_fan"]),int(cs.grow_params["Dt_fan"]),int(cs.grow_params["Dh_fan"])))
            if cs.feature_toggles["light"] == "1":
                run_light(int(cs.grow_params["time_start_light"]), int(cs.grow_params["time_stop_light"]), int(cs.grow_params["lighting_interval"]))
            if cs.feature_toggles["camera"] == "1":
                run_camera(int(cs.grow_params["camera_interval"]))
            if cs.feature_toggles["water"] == "1":
                run_water(int(cs.grow_params["watering_duration"]),int(cs.grow_params["watering_interval"]))
            if cs.feature_toggles["air"] == "1":
                run_air(int(cs.grow_params["time_start_air"]), int(cs.grow_params["time_stop_air"]),  int(cs.grow_params["air_interval"]))

            #set exit condition    
            cs.load_state()
            if cs.device_state["running"] == "0":
                terminate_program()
            else:
                pass

            #give the program some time to breathe
            time.sleep(1)

    except (KeyboardInterrupt):
        terminate_program()

    except Exception as e:
        traceback.print_exc()
        if cs.device_state["running"] == "1": #if there is an error, but device should stay running
            clean_up_processes()
        if cs.device_state["running"] == "0":
            terminate_program()
            
if __name__ == '__main__':
    main_setup()
    main_loop()

