#---------------------------------------------------------------------------------------
#IMPORTS
#Shell, PID, Communication, Time
#---------------------------------------------------------------------------------------
#Setup Path
import os
import os.path
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
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
import pandas

#dealing with specific times of the day
import time
import datetime

#declare state variables
device_state = None #describes the current state of the system
access_config = None #contains credentials for connecting to firebase
feature_toggles = None #tells grow_ctrl which elements are active and which are not
grow_params = None #offers run parameters to oasis-grow

#declare process management variables
ser_in = None
sensor_info = None
heat_process = None
humidity_process = None
fan_process = None
light_process = None
camera_process = None
water_process = None
air_process = None

#declare sensor data variables
temperature = 0
humidity = 0
last_temperature = 0
last_humidity = 0
last_target_temperature = 0
last_target_humidity = 0
water_low = 0

#timekeeping variables
data_timer = None
sensor_log_timer = None

#loads device state, hardware, and access configurations
#checks first to see that main is not writing, if json valid, loads state
def load_state(): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, feature_toggles, access_config, grow_params

    #verify that the child is not current writing

    try:
        with open("/home/pi/oasis-grow/configs/device_state.json") as d:
            device_state = json.load(d) #get device state

        with open("/home/pi/oasis-grow/configs/grow_params.json") as g:
            grow_params = json.load(g) #get grow params

        with open("/home/pi/oasis-grow/configs/access_config.json") as a:
            access_config = json.load(a) #get access state

        with open ("/home/pi/oasis-grow/configs/feature_toggles.json") as f:
            feature_toggles = json.load(f) #get feature toggles

    except Exception as e:
        print("Tried to read while a write was occuring. Retrying...")
        load_state()

#modifies a firebase variable
def patch_firebase(dict): #Depends on: load_state(),'requests','json'; Modifies: database{data}, state variables
    load_state()
    data = json.dumps(dict)
    url = "https://oasis-1757f.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)

#save key values to .json
def write_state(path,field,value, loop_limit=100000): #Depends on: load_state(), patch_firebase, 'json'; Modifies: path
    load_state()

    #these will be loaded in by the listener, so best to make sure we represent the change in firebase too
    if device_state["connected"] == "1": #write state to cloud
        try:
            dict = {str(field):str(value)}
            patch_firebase(dict)
        except Exception as e:
            print(e)
            pass

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open(path, "r+") as x: # open the file.
                data = json.load(x) # can we load a valid json?

                if path == "/home/pi/oasis-grow/configs/device_state.json": #are we working in device_state?
                    if data["device_state_write_available"] == "1": #check is the file is available to be written
                        data["device_state_write_available"] = "0" #let system know resource is not available
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        data[field] = value #write the desired value
                        data["device_state_write_available"] = "1" #let system know resource is available again 
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        break #break the loop when the write has been successful

                    else:
                        pass

                elif path == "/home/pi/oasis-grow/configs/grow_params.json": #are we working in grow_params?
                    if data["grow_params_write_available"] == "1":
                        data["grow_params_write_available"] = "0" #let system know writer is not available
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        data["grow_params_write_available"] = "1"
                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        break  #break the loop when the write has been successful

                else: #otherwise, attempt a normal write
                    data[field] = value #write the desired value
                    x.seek(0)
                    json.dump(data, x)
                    x.truncate()

                    break #break the loop when the write has been successful

        except Exception as e: #If any of the above fails:
            print("Tried to write while another write was occuring, retrying...")
            print(e)
            pass #continue the loop until write is successful or cieling is hit

#write some data to a .csv, takes a dictionary and a path
def write_csv(path, dict): #Depends on: 'pandas',
    #load dict into dataframe
    df = pandas.DataFrame(dict)
    #.csv write
    df.to_csv(str(path), sep='\t', header=None, mode='a+')

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
        #ser_in = None
        print("Serial connection not found")

#gets data from serial THIS WILL HAVE TO BE DEPRECATED SOON IN FAVOR OF AN ON-BOARD SENSOR SUITE
def listen(): #Depends on 'serial', start_serial(); Modifies: ser_in, sensor_info, temperature, humidity, last_temperature, last_humidity, water_low
    #load in global vars
    global ser_in,sensor_info,temperature,humidity,last_temperature,last_humidity,water_low

    if ser_in == None:
        return

    #listen for data from aurdino
    sensor_info = ser_in.readline().decode('UTF-8').strip().split(' ')

    if len(sensor_info)<3:
        pass
    else:
        #print and save our data
        last_humidity = humidity
        humidity =float(sensor_info[0])

        last_temperature = temperature
        temperature =float(sensor_info[1])

        water_low = int(sensor_info[2])

#PD controller to modulate heater feedback
def heat_pd(temperature, target_temperature, last_temperature, last_target_temperature, P_heat, D_heat): #no dependencies
    err_temperature = target_temperature-temperature

    temperature_dot = temperature-last_temperature

    target_temperature_dot = target_temperature-last_target_temperature

    err_dot_temperature = target_temperature_dot-temperature_dot

    heat_level  = P_heat*err_temperature + D_heat*err_dot_temperature
    heat_level  = max(min(int(heat_level),100),0)

    return heat_level

#PD controller to modulate humidifier feedback
def hum_pd(humidity, target_humidity, last_humidity, last_target_humidity, P_hum, D_hum): #no dependencies
    err_humidity = target_humidity-humidity

    humidity_dot = humidity-last_humidity

    target_humidity_dot = target_humidity-last_target_humidity

    err_dot_humidity = target_humidity_dot-humidity_dot

    humidity_level  = P_hum*err_humidity + D_hum*err_dot_humidity
    humidity_level  = max(min(int(humidity_level),100),0)

    return humidity_level

#PD controller to modulate fan feedback
def fan_pd(temperature, humidity, target_temperature, target_humidity, last_temperature, last_humidity, last_target_temperature, last_target_humidity, Pt_fan, Ph_fan, Dt_fan, Dh_fan): #no dependencies
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
    load_state()

    if (feature_toggles["heater"] == "1") and (heat_process != None): #go through toggles and kill active processes
        heat_process.terminate()
        heat_process.wait()

    if (feature_toggles["humidifier"] == "1") and (humidity_process != None):
        humidity_process.terminate()
        humidity_process.wait()

    if (feature_toggles["fan"] == "1") and (fan_process != None):
        fan_process.terminate()
        fan_process.wait()

    if (feature_toggles["light"] == "1") and (light_process != None):
        light_process.terminate()
        light_process.wait()

    if (feature_toggles["camera"] == "1") and (camera_process != None):
        camera_process.terminate()
        camera_process.wait()

    if (feature_toggles["water"] == "1") and (water_process != None):
        water_process.terminate()
        water_process.wait()

    if (feature_toggles["air"] == "1") and (air_process != None):
        air_process.terminate()
        air_process.wait()

    gc.collect()

#terminates the program and all running subprocesses
def terminate_program(): #Depends on: load_state(), 'sys', 'subprocess' #Modifies: heat_process, humidity_process, fan_process, light_process, camera_process, water_process

    print("Terminating Program...")
    clean_up_processes()

    #flip "running" to 0
    write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "0")

    sys.exit()

def main_setup():
    global data_timer, sensor_log_timer

    #Load state variables to start the main program
    load_state()

    #Exit early if opening subprocess daemon
    if str(sys.argv[1]) == "daemon":
        print("grow_ctrl daemon started")
        #log daemon start
        write_state('/home/pi/oasis-grow/data_out/logs/grow_ctrl_log.json','last_start_mode',"daemon")
        #kill the program
        sys.exit()
    if str(sys.argv[1]) == "main":
        print("grow_ctrl main started")
        #log main start
        write_state('/home/pi/oasis-grow/data_out/logs/grow_ctrl_log.json','last_start_mode',"main")
        #flip "running" to 1 to make usable from command line
        write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "1")
        #continue with program execution
        pass
    else:
        print("please offer valid run parameters")
        sys.exit()

    #attempt to make serial connection
    start_serial()

    #start the clock for timimg .csv writes and data exchanges with server
    data_timer = time.time()
    sensor_log_timer = time.time()

def main_loop():
    global data_timer, sensor_log_timer, last_target_temperature, last_target_humidity, device_state

    #launch main program loop
    try:
        print("------------------------------------------------------------")

        while True:

            last_target_temperature = int(grow_params["target_temperature"]) #save last temperature and humidity targets to calculate delta for PD controllers
            last_target_humidity = int(grow_params["target_humidity"])

            load_state() #regresh the state variables to get new parameters


            if (feature_toggles["temp_hum_sensor"] == "1") or (feature_toggles["water_low_sensor"] == "1"):
                try: #attempt to read data from sensor, raise exception if there is a problem
                    listen() #this will be changed to run many sensor functions as opposed to one serial listener
                except Exception as e:
                    print(e)
                    print("Serial Port Failure")

            if feature_toggles["heater"] == "1":
                print("Target Temperature: %.1f F | Current: %.1f F | Temp_PID: %s %%"%(int(grow_params["target_temperature"]),temperature, heat_pd(temperature,
                                                                                                                                  int(grow_params["target_temperature"]),
                                                                                                                                  last_temperature,
                                                                                                                                  last_target_temperature,
                                                                                                                                  int(grow_params["P_temp"]),
                                                                                                                                  int(grow_params["D_temp"]))))
            if feature_toggles["humidifier"] == "1":
                print("Target Humidity: %.1f %% | Current: %.1f %% | Hum_PID: %s %%"%(int(grow_params["target_humidity"]), humidity, hum_pd(humidity,
                                                                                                                               int(grow_params["target_humidity"]),
                                                                                                                               last_humidity,
                                                                                                                               last_target_humidity,
                                                                                                                               int(grow_params["P_hum"]),
                                                                                                                               int(grow_params["D_hum"]))))

            if feature_toggles["fan"] == "1":
                print("Fan PD: %s %%"%(fan_pd(temperature,
                                              humidity,
                                              int(grow_params["target_temperature"]),
                                              int(grow_params["target_humidity"]),
                                              last_temperature,
                                              last_humidity,
                                              last_target_temperature,
                                              last_target_humidity,
                                              int(grow_params["Pt_fan"]),
                                              int(grow_params["Ph_fan"]),
                                              int(grow_params["Dt_fan"]),
                                              int(grow_params["Dh_fan"]))))

            if feature_toggles["light"] == "1":
                print("Light Turns on at: %i :00 Local Time  | Turns off at: %i :00 Local Time"%(int(grow_params["time_start_light"]), int(grow_params["time_start_dark"])))

            if feature_toggles["camera"] == "1":
                print("Image every %i minute(s)"%(int(grow_params["camera_interval"])))

            if feature_toggles["water"] == "1":
                print("Watering for: %i second(s) every: %i hour(s)"%(int(grow_params["watering_duration"]), int(grow_params["watering_interval"])))

            if feature_toggles["water_low_sensor"] == "1":
                if water_low == 1:
                    print("Water Level Low!")

            print("------------------------------------------------------------")

            #every hour, log past hour and shift 24 hours of sensor data
            if time.time() - sensor_log_timer > 5:

                if feature_toggles["temp_hum_sensor"] == "1":

                    print("Entering temp & hum logging")

                    #extract workable dictionary from json string
                    device_state["temperature_log"] = eval(device_state["temperature_log"])
                    device_state["humidity_log"] = eval(device_state["humidity_log"])
                    
                    #replace each log with the next most recent one
                    device_state["temperature_log"][23] = device_state["temperature_log"][22]
                    device_state["temperature_log"][22] = device_state["temperature_log"][21]
                    device_state["temperature_log"][21] = device_state["temperature_log"][20]
                    device_state["temperature_log"][20] = device_state["temperature_log"][19]
                    device_state["temperature_log"][19] = device_state["temperature_log"][18]
                    device_state["temperature_log"][18] = device_state["temperature_log"][17]
                    device_state["temperature_log"][17] = device_state["temperature_log"][16]
                    device_state["temperature_log"][16] = device_state["temperature_log"][15]
                    device_state["temperature_log"][15] = device_state["temperature_log"][14]
                    device_state["temperature_log"][14] = device_state["temperature_log"][13]
                    device_state["temperature_log"][13] = device_state["temperature_log"][12]
                    device_state["temperature_log"][12] = device_state["temperature_log"][11]
                    device_state["temperature_log"][11] = device_state["temperature_log"][10]
                    device_state["temperature_log"][10] = device_state["temperature_log"][9]
                    device_state["temperature_log"][9] = device_state["temperature_log"][8]
                    device_state["temperature_log"][8] = device_state["temperature_log"][7]
                    device_state["temperature_log"][7] = device_state["temperature_log"][6]
                    device_state["temperature_log"][6] = device_state["temperature_log"][5]
                    device_state["temperature_log"][5] = device_state["temperature_log"][4]
                    device_state["temperature_log"][4] = device_state["temperature_log"][3]
                    device_state["temperature_log"][3] = device_state["temperature_log"][2]
                    device_state["temperature_log"][2] = device_state["temperature_log"][1]
                    device_state["temperature_log"][1] = device_state["temperature_log"][0]
                    
                    device_state["humidity_log"][23] = device_state["humidity_log"][22]
                    device_state["humidity_log"][22] = device_state["humidity_log"][21]
                    device_state["humidity_log"][21] = device_state["humidity_log"][20]
                    device_state["humidity_log"][20] = device_state["humidity_log"][19]
                    device_state["humidity_log"][19] = device_state["humidity_log"][18]
                    device_state["humidity_log"][18] = device_state["humidity_log"][17]
                    device_state["humidity_log"][17] = device_state["humidity_log"][16]
                    device_state["humidity_log"][16] = device_state["humidity_log"][15]
                    device_state["humidity_log"][15] = device_state["humidity_log"][14]
                    device_state["humidity_log"][14] = device_state["humidity_log"][13]
                    device_state["humidity_log"][13] = device_state["humidity_log"][12]
                    device_state["humidity_log"][12] = device_state["humidity_log"][11]
                    device_state["humidity_log"][11] = device_state["humidity_log"][10]
                    device_state["humidity_log"][10] = device_state["humidity_log"][9]
                    device_state["humidity_log"][9] = device_state["humidity_log"][8]
                    device_state["humidity_log"][8] = device_state["humidity_log"][7]
                    device_state["humidity_log"][7] = device_state["humidity_log"][6]
                    device_state["humidity_log"][6] = device_state["humidity_log"][5]
                    device_state["humidity_log"][5] = device_state["humidity_log"][4]
                    device_state["humidity_log"][4] = device_state["humidity_log"][3]
                    device_state["humidity_log"][3] = device_state["humidity_log"][2]
                    device_state["humidity_log"][2] = device_state["humidity_log"][1]
                    device_state["humidity_log"][1] = device_state["humidity_log"][0]

                    #save new data to 1 hour ago
                    device_state["temperature_log"][0] = str(temperature)
                    device_state["humidity_log"][0] = str(humidity)
                    
                    #convert data back to json string
                    device_state["temperature_log"] = json.dump(device_state["temperature_log"])
                    device_state["humidity_log"] = json.dump(device_state["humidity_log"])
                    
                    #push data to local json too
                    write_state("/home/pi/oasis-grow/configs/device_state.json", "temperature_log", device_state["temperature_log"])
                    write_state("/home/pi/oasis-grow/configs/device_state.json", "humidity_log", device_state["humidity_log"])

                #start clock
                sensor_log_timer = time.time()

            #write data and send to server after set time elapses
            if time.time() - data_timer > 300:

                try:

                    if feature_toggles["save_data"] == "1":
                        #save data to .csv
                        print("Writing to csv")
                        write_csv('/home/pi/oasis-grow/data_out/sensor_feed/sensor_data.csv',{"time": [str(time.time())], "temperature": [str(temperature)], "humidity": [str(humidity)], "water_low": [str(water_low)]})

                    write_state("/home/pi/oasis-grow/configs/device_state.json", "temperature", str(temperature))
                    write_state("/home/pi/oasis-grow/configs/device_state.json", "humidity", str(humidity))
                    write_state("/home/pi/oasis-grow/configs/device_state.json", "water_low", str(water_low))

                    data_timer = time.time()

                except Exception as e:
                    print(e)
                    data_timer = time.time()

            #update actuators in use
            if feature_toggles["heater"] == "1":
                run_heat(str(heat_pd(temperature,int(grow_params["target_temperature"]),last_temperature,last_target_temperature,int(grow_params["P_temp"]),int(grow_params["D_temp"]))))
            if feature_toggles["humidifier"] == "1":
                run_hum(str(hum_pd(humidity,int(grow_params["target_humidity"]),last_humidity,last_target_humidity,int(grow_params["P_hum"]),int(grow_params["D_hum"]))))
            if feature_toggles["fan"] == "1":
                run_fan(fan_pd(temperature,humidity,int(grow_params["target_temperature"]),int(grow_params["target_humidity"]),last_temperature,last_humidity,last_target_temperature,last_target_humidity,int(grow_params["Pt_fan"]),int(grow_params["Ph_fan"]),int(grow_params["Dt_fan"]),int(grow_params["Dh_fan"])))
            if feature_toggles["light"] == "1":
                run_light(int(grow_params["time_start_light"]), int(grow_params["time_start_dark"]), int(grow_params["lighting_interval"]))
            if feature_toggles["camera"] == "1":
                run_camera(int(grow_params["camera_interval"]))
            if feature_toggles["water"] == "1":
                run_water(int(grow_params["watering_duration"]),int(grow_params["watering_interval"]))
            if feature_toggles["air"] == "1":
            	run_air(int(grow_params["time_start_air"]), int(grow_params["time_stop_air"]),  int(grow_params["air_interval"]))

            #set exit condition
            load_state()
            if device_state["running"] == "0":
                terminate_program()
            else:
                pass

            #give the program some time to breathe
            time.sleep(1)

    except (KeyboardInterrupt):
        terminate_program()

    except Exception as e:
        traceback.print_exc()
        if device_state["running"] == "1": #if there is an error, but device should stay running
            #clean_up_processes()
            terminate_program()
        if device_state["running"] == "0":
            #terminate_program()
            terminate_program()
            
if __name__ == '__main__':
    main_setup()
    main_loop()

