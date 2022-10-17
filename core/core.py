#Yes, I understand the core is a procedural mess. It runs without bugs, for now
#We're working on refactoring this to an object oriented and functional approach in v2
#This will make it easier to and add new features, expand existing ones, and change behavior.

#system
import os
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#Process management
import signal
import rusty_pipes

#data handling
import orjson
import csv
import math
import pprint

#dealing with specific times of the day
import time
import datetime

#import other oasis packages
from utils import concurrent_state as cs
from utils import error_handler as err
from networking import db_tools as dbt
from peripherals import microcontroller_manager as minion

resource_name = "core"

#declare sensor data variables
temperature = 0
last_temperature = 0
last_target_temperature = 0
err_cum_temperature = 0

humidity = 0
last_humidity = 0
last_target_humidity = 0
err_cum_humidity = 0

co2 = 0
last_co2 = 0
last_target_co2 = 0
err_cum_co2 = 0

substrate_moisture = 0
last_substrate_moisture = 0
last_target_substrate_moisture = 0
err_cum_substrate_moisture = 0

water_low = 0
vpd = 0
lux = 0
ph = 0
tds = 0

#actuator output variables
temp_feedback = 0
hum_feedback = 0
dehum_feedback = 0
fan_feedback = 0
water_feedback = 0

#subprocess vars
heat_process = None
humidity_process = None
dehumidify_process = None
fan_process = None
light_process = None
camera_process = None
water_process = None
air_process = None

#timekeeping variables
data_timer = None

#write some data to a .csv, takes a dictionary and a path
def write_csv(filename, dict): #Depends on: "os" "csv"
    file_exists = os.path.isfile(filename)

    with open (filename, 'a') as csvfile:
        headers = ["time"]

        if cs.structs["feature_toggles"]["temperature_sensor"] == "1":
            headers.append("temperature")
        if cs.structs["feature_toggles"]["humidity_sensor"] == "1":
            headers.append("humidity")
        if cs.structs["feature_toggles"]["co2_sensor"] == "1":
            headers.append("co2")
        if cs.structs["feature_toggles"]["substrate_moisture_sensor"] == "1":
            headers.append("substrate_moisture")
        if cs.structs["feature_toggles"]["vpd_calculation"] == "1":
            headers.append("vpd")
        if cs.structs["feature_toggles"]["water_level_sensor"] == "1":
            headers.append("water_low")
        if cs.structs["feature_toggles"]["lux_sensor"] == "1":
            headers.append("lux")
        if cs.structs["feature_toggles"]["ph_sensor"] == "1":
            headers.append("ph")
        if cs.structs["feature_toggles"]["tds_sensor"] == "1":
            headers.append("tds")

        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header

        variables = {}

        for variable in dict.keys():
            if variable in headers:
                variables[variable] = dict[variable]

        writer.writerow(variables)

        writer = None

    return

def send_csv(path):
    #send new image to firebase
    cs.load_state()
    user, db, storage = dbt.initialize_user(cs.structs["access_config"]["refresh_token"])
    dbt.store_file(user, storage, path, cs.structs["access_config"]["device_name"], "sensor_data.csv")
    print("Sent csv timeseries")

    #tell firebase that there is a new time series
    dbt.patch_firebase(cs.structs["access_config"], "csv_sent", "1")
    print("Firebase has a time-series in waiting")

#gets data from serial, will parse a simple string or accept a dictionary
def listen(): #Depends on 'serial', start_serial()
    global minion, temperature,  humidity,  co2,  substrate_moisture, vpd, water_low, lux, ph, tds  
    global last_temperature, last_humidity, last_co2, last_substrate_moisture #past readings for derivative calculations
    #print("hey I just met you")
    if minion.ser_in == None:
        print("ser_in is none")
        return 
        
    #print("and this is crazy")
    
    try:
        sensor_data = orjson.loads(minion.ser_in.readline().decode('UTF-8').strip().encode())
        #print(sensor_data)
        #print("but here's my number")
        if cs.structs["feature_toggles"]["temperature_sensor"] == "1":
            last_temperature = temperature
            temperature = float(sensor_data["temperature"]) + float(cs.structs["sensor_info"]["temperature_calibration"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "temperature", str(temperature), db_writer = None)      
        if cs.structs["feature_toggles"]["humidity_sensor"] == "1":
            last_humidity = humidity
            humidity = float(sensor_data["humidity"]) + float(cs.structs["sensor_info"]["humidity_calibration"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "humidity", str(humidity), db_writer = None)
        if cs.structs["feature_toggles"]["co2_sensor"] == "1":
            last_co2 = co2
            co2 = float(sensor_data["co2"]) + float(cs.structs["sensor_info"]["co2_calibration"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "co2", str(co2), db_writer = None)
        if cs.structs["feature_toggles"]["substrate_moisture_sensor"] == "1":
            last_substrate_moisture = substrate_moisture
            substrate_moisture = float(sensor_data["substrate_moisture"]) + float(cs.structs["sensor_info"]["substrate_moisture_calibration"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "substrate_moisture", str(substrate_moisture), db_writer = None)
        if cs.structs["feature_toggles"]["lux_sensor"] == "1":
            lux = float(sensor_data["lux"]) + float(cs.structs["sensor_info"]["lux_calibration"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "lux", str(lux), db_writer = None)
        if cs.structs["feature_toggles"]["ph_sensor"] == "1":
            ph = float(sensor_data["ph"]) + float(cs.structs["sensor_info"]["ph_calibration"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "ph", str(ph), db_writer = None)
        if cs.structs["feature_toggles"]["tds_sensor"] == "1":
            tds = float(sensor_data["tds"]) + float(cs.structs["sensor_info"]["tds_calibration"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "tds", str(tds), db_writer = None)

        if cs.structs["feature_toggles"]["vpd_calculation"] == "1":
            f = float(temperature) #temperature farenheit
            t =	(5/9)*(f + 459.67) #temperature kelvin
            rh =  float(humidity) #relative humidity
            #https://www.cs.helsinki.fi/u/ssmoland/physics/envphys/lecture_2.pdf
            a = 77.34 #empirically
            b = -7235 #fitted
            c = -8.2 #exponental
            d = 0.005711 #constants
            svp = math.e ** (a+(b/t)+(c*math.log(t))+d*t) #saturation vapor pressure
            #https://agradehydroponics.com/blogs/a-grade-news/how-to-calculate-vapour-pressure-deficit-vpd-via-room-temperature
            vpd_pa = (1 - (rh/100)) * svp #vapor pressure deficit in pascals
            vpd = vpd_pa / 1000 #convert vpd to kilopascals
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "vpd", str(vpd), db_writer = None)
        
        if cs.structs["feature_toggles"]["water_level_sensor"] == "1":
            water_low = int(sensor_data["water_low"])
            cs.write_state("/home/pi/oasis-grow/configs/sensor_info.json", "water_low", str(water_low), db_writer = None)
    except:
        print(err.full_stack()) #uncomment to debug listener
        pass

def smart_listener():
    if ((cs.structs["feature_toggles"]["temperature_sensor"] == "1") \
                or (cs.structs["feature_toggles"]["humidity_sensor"] == "1") \
                    or (cs.structs["feature_toggles"]["water_level_sensor"] == "1") \
                        or (cs.structs["feature_toggles"]["co2_sensor"] == "1") \
                            or (cs.structs["feature_toggles"]["lux_sensor"] == "1") \
                                or (cs.structs["feature_toggles"]["ph_sensor"] == "1") \
                                    or (cs.structs["feature_toggles"]["tds_sensor"] == "1") \
                                        or (cs.structs["feature_toggles"]["substrate_moisture_sensor"] == "1")):
        try: #attempt to read data from sensor, raise exception if there is a problem
            #print("Smart listener is attempting to collect data from arduino")
            listen() #this will be changed to run many sensor functions as opposed to one serial listener
        except Exception as e:
            print(err.full_stack())
            print("Listener Failure")

def update_derivative_banks():
    global last_target_temperature, last_target_humidity, last_target_co2, last_target_substrate_moisture

    #save last temperature and humidity targets to calculate delta for PD controllers
    last_target_temperature = float(cs.structs["device_params"]["target_temperature"]) 
    last_target_humidity = float(cs.structs["device_params"]["target_humidity"])
    last_target_co2 = float(cs.structs["device_params"]["target_co2"])
    last_target_substrate_moisture = float(cs.structs["device_params"]["target_substrate_moisture"])

#PID controller to modulate heater feedback
def heat_pid(temperature, target_temperature, last_temperature, last_target_temperature,
             P_heat, I_heat, D_heat):    
    
    global err_cum_temperature

    err_temperature = target_temperature-temperature    #If target is 70 and temperature is 60, this value = 10, more heat
                                                        #If target is 50 and temperature is 60, this value is negative, less heat

    temperature_dot = temperature-last_temperature  #If temp is increasing, this value is positive (+#)
                                                    #If temp is decreasing, this value is negative (-#)

    err_cum_temperature = max(min(err_cum_temperature + err_temperature, 50), -50)

    target_temperature_dot = target_temperature-last_target_temperature #When target remains the same, this value is 0
                                                                        #When adjusting target up, this value is positive (+#)
                                                                        #When adjusting target down, this value is negative (-#)

    err_dot_temperature = target_temperature_dot-temperature_dot    #When positive, boosts heat signal
                                                                    #When negative, dampens heat signal
    heat_level  = P_heat * err_temperature + I_heat * err_cum_temperature + D_heat * err_dot_temperature
    heat_level  = max(min(int(heat_level), 100), 0)
    print(heat_level)

    return heat_level

#PID controller to modulate humidifier feedback, feedback pushes up towards target
def hum_pid(humidity, target_humidity, last_humidity, last_target_humidity, 
            P_hum, I_hum, D_hum):
    
    global err_cum_humidity
    
    err_humidity = target_humidity - humidity

    humidity_dot = humidity - last_humidity

    err_cum_humidity = max(min(err_cum_humidity + err_humidity, 50), -50)

    target_humidity_dot = target_humidity - last_target_humidity

    err_dot_humidity = target_humidity_dot - humidity_dot

    humidity_level  = P_hum*err_humidity + I_hum*err_cum_humidity + D_hum*err_dot_humidity #positive response
    humidity_level  = max(min(int(humidity_level),100),0)
    print(humidity_level)

    return humidity_level

#PID controller to modulate dehumidifier feedback pushes down towards target
def dehum_pid(humidity, target_humidity, last_humidity, last_target_humidity,
              P_dehum, I_dehum, D_dehum):
    
    global err_cum_humidity

    err_humidity = target_humidity - humidity
                                                
    humidity_dot = humidity - last_humidity 

    if cs.structs["feature_toggles"]["hum_pid"] == "0":
        err_cum_humidity = max(min(err_cum_humidity + err_humidity, 50), -50) 

    target_humidity_dot = target_humidity - last_target_humidity

    err_dot_humidity = target_humidity_dot - humidity_dot

    dehumidify_level  = (0-P_dehum)*err_humidity + (0-I_dehum)*err_cum_humidity + (0-D_dehum)*err_dot_humidity
    dehumidify_level  = max(min(int(dehumidify_level), 100), 0)
    print(dehumidify_level)

    return dehumidify_level

#PID controller to modulate fan feedback, pushes down temp, hum, & c02 towards target
def fan_pid(temperature, humidity, co2,
            target_temperature, target_humidity, target_co2,
            last_temperature, last_humidity, last_co2,
            last_target_temperature, last_target_humidity, last_target_co2,
            Pt_fan, It_fan, Dt_fan, Ph_fan, Ih_fan, Dh_fan, Pc_fan, Ic_fan, Dc_fan):
    
    global err_cum_temperature, err_cum_humidity, err_cum_co2
    
    err_temperature = target_temperature - temperature
    err_humidity = target_humidity - humidity
    err_co2 = target_co2 - co2

    temperature_dot = temperature-last_temperature
    humidity_dot = humidity-last_humidity
    co2_dot = co2 - last_co2

    if cs.structs["feature_toggles"]["heat_pid"] == "0":
        err_cum_temperature = max(min(err_cum_temperature + err_temperature, 50), -50)

    if (cs.structs["feature_toggles"]["hum_pid"] == "0") and (cs.structs["feature_toggles"]["dehum_pid"] == "0"):
        err_cum_humidity = max(min(err_cum_humidity + err_humidity, 50), -50)

    err_cum_co2 = max(min(err_cum_humidity + err_humidity, 50), -50)

    target_temperature_dot = target_temperature - last_target_temperature
    target_humidity_dot = target_humidity - last_target_humidity
    target_co2_dot = target_co2 - last_target_co2

    err_dot_temperature = target_temperature_dot - temperature_dot
    err_dot_humidity = target_humidity_dot - humidity_dot
    err_dot_co2 = target_co2_dot - co2_dot

    fan_level  = (0-Pt_fan)*err_temperature + (0-It_fan)*err_cum_temperature + (0-Dt_fan)*err_dot_temperature \
                +(0-Ph_fan)*err_humidity + (0-Ih_fan)*err_cum_humidity + (0-Dh_fan)*err_dot_humidity \
                +(0-Pc_fan)*err_co2 + (0-Ic_fan)*err_cum_co2 + (0-Dc_fan)*err_dot_co2    
    
    fan_level  = max(min(int(fan_level),100),0)
    print(fan_level)

    return fan_level

#PID controller to modulate heater feedback
def water_pid(substrate_moisture, target_substrate_moisture, 
              last_substrate_moisture, last_target_substrate_moisture,
              P_moisture, I_moisture, D_moisture):    
    
    global err_cum_substrate_moisture

    err_substrate_moisture = target_substrate_moisture - substrate_moisture   #If target is 70 and temperature is 60, this value = 10, more heat
                                                        #If target is 50 and temperature is 60, this value is negative, less heat

    substrate_moisture_dot = substrate_moisturesture-substsubstrate_moisturesture  #If temp is increasing, this value is positive (+#)
                                                    #If temp is decreasing, this value is negative (-#)

    err_cum_substrate_moisturesture = max(min(err_cum_substrate_moisture + err_substrate_moisture, 50), -50)

    target_substrate_moisture_dot = target_substrate_moisture-last_target_substrate_moisture #When target remains the same, this value is 0
                                                                        #When adjusting target up, this value is positive (+#)
                                                                        #When adjusting target down, this value is negative (-#)

    err_dot_substrate_moisture = target_substrate_moisture_dot-substrate_moisture_dot    #When positive, boosts heat signal
                                                                    #When negative, dampens heat signal
    water_level  = P_moisture * err_substrate_moisture \
                   + I_moisture * err_cum_substrate_moisture \
                   + D_moisture * err_dot_substrate_moisture
    
    water_level  = max(min(int(water_level), 100), 0)
    print(water_level)

    return water_level

#Concurrency Hell:
#
#   Ok, so the subprocess will always relaunch itself on every loop right now, because
#   even when it exits the process will always retain some information in memory about its exit
#   because a reference still exists according to the python garbage collector. This does not happen
#   at first because the processes start as None, and because the memory is never cleared:
#   process.exited() sometimes returns True when queried even though there is something also running.
#   
#   Solution: Use the system level mutex you've already built, get rid of the global variable.
#   Simple Version: Check the lock, don't poll the process.

#poll heat subprocess if applicable and relaunch/update equipment
def run_heat(intensity = 0):
    global heat_process

    resource_name =  "heater"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        if cs.structs["feature_toggles"]["heat_pid"] == "1":
            heat_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/heater.py', str(intensity)]) #If process not free, then skips.
        else:
            heat_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/heater.py', cs.structs["device_params"]["heater_duration"], cs.structs["device_params"]["heater_interval"]]) #If process not free, then skips.


#poll humidityf subprocess if applicable and relaunch/update equipment
def run_hum(intensity = 0):
    global humidity_process

    resource_name =  "humidifier"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        if cs.structs["feature_toggles"]["hum_pid"] == "1":
            humidity_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/humidifier.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
        else:
            humidity_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/humidifier.py', cs.structs["device_params"]["humidifier_duration"], cs.structs["device_params"]["humidifier_interval"]])
    
#poll dehumidify subprocess if applicable and relaunch/update equipment
def run_dehum(intensity = 0):
    global dehumidify_process

    resource_name =  "dehumidifier"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        if cs.structs["feature_toggles"]["dehum_pid"] == "1":
            dehumidify_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/dehumidifier.py', str(intensity)]) #If running, then skips. If idle then restarts, If no process, then fails
        else:
            dehumidify_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/dehumidifier.py', cs.structs["device_params"]["dehumidifier_duration"], cs.structs["device_params"]["dehumidifier_interval"]])

#poll fan subprocess if applicable and relaunch/update equipment
def run_fan(intensity = 0): #Depends on: 'subprocess'; Modifies: humidity_process
    global fan_process
    
    resource_name =  "fan"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        if cs.structs["feature_toggles"]["fan_pid"] == "1":
            fan_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/fan.py', str(intensity)]) 
        else:
            fan_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/fan.py', cs.structs["device_params"]["fan_duration"], cs.structs["device_params"]["fan_interval"]])

#poll water subprocess if applicable and relaunch/update equipment
def run_water(intensity = 0): #Depends on: 'subprocess'; Modifies: water_process
    global water_process
    
    resource_name =  "water_pump"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        if cs.structs["feature_toggles"]["water_pid"] == "1":
            water_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/water_pump.py', str(intensity)])
        else:
            water_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/water_pump.py', str(cs.structs["device_params"]["watering_duration"]), str(cs.structs["device_params"]["watering_interval"])]) #If running, then skips. If idle then restarts.
    
#poll light subprocess if applicable and relaunch/update equipment
def run_light():
    global light_process
    
    resource_name =  "lights"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        light_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/lights.py', cs.structs["device_params"]["time_start_light"], cs.structs["device_params"]["time_stop_light"], cs.structs["device_params"]["lighting_interval"]]) #If running, then skips. If free then restarts.
   
#poll air subprocess if applicable and relaunch/update equipment
def run_air():
    global air_process
    
    resource_name =  "air_pump"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        air_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/equipment/air_pump.py', cs.structs["device_params"]["time_start_air"], cs.structs["device_params"]["time_stop_air"], cs.structs["device_params"]["air_interval"]]) #If running, then skips. If idle then restarts.
    
#poll camera subprocess if applicable and relaunch/update equipment
def run_camera(): #Depends on: 'subprocess'; Modifies: camera_process
    global camera_process

    resource_name =  "camera"
    cs.load_locks()
    if cs.locks[resource_name] == 0:
        camera_process = rusty_pipes.Open(['python3', '/home/pi/oasis-grow/imaging/camera.py', cs.structs["hardware_config"]["camera_settings"]["picture_frequency"]]) #If running, then skips. If idle then restarts.

def run_active_equipment():
    
    global temp_feedback, hum_feedback, dehum_feedback, fan_feedback, water_feedback

    # calculate feedback levels and update equipment in use
    if cs.structs["feature_toggles"]["heater"] == "1":
        if cs.structs["feature_toggles"]["heat_pid"] == "1": #computes a feedback value if PID is on
            temp_feedback = int(heat_pid(temperature,
                                        int(cs.structs["device_params"]["target_temperature"]),
                                        last_temperature,
                                        last_target_temperature,
                                        int(cs.structs["device_params"]["P_heat"]),
                                        int(cs.structs["device_params"]["I_heat"]),
                                        int(cs.structs["device_params"]["D_heat"])))
        run_heat(temp_feedback) #this function always takes a feedback value
                                #but it runs differently when pid is off in feature toggles
                                #the way it runs is dependent on the external configuration
                                #if PID is off, it runs using timer values in device_params
                                #all PID enables functions work the same, so they can be used
                                #without actuators
    
    if cs.structs["feature_toggles"]["humidifier"] == "1":
        if cs.structs["feature_toggles"]["hum_pid"] == "1":
            hum_feedback = int(hum_pid(humidity,
                                        int(cs.structs["device_params"]["target_humidity"]),
                                        last_humidity,
                                        last_target_humidity,
                                        int(cs.structs["device_params"]["P_hum"]),
                                        int(cs.structs["device_params"]["I_hum"]),
                                        int(cs.structs["device_params"]["D_hum"])))
        run_hum(hum_feedback)
    
    if cs.structs["feature_toggles"]["dehumidifier"] == "1":
        if cs.structs["feature_toggles"]["dehum_pid"] == "1":
            dehum_feedback = int(dehum_pid(humidity,
                                        int(cs.structs["device_params"]["target_humidity"]),
                                        last_humidity,
                                        last_target_humidity,
                                        int(cs.structs["device_params"]["P_dehum"]),
                                        int(cs.structs["device_params"]["I_dehum"]),
                                        int(cs.structs["device_params"]["D_dehum"])))
        run_dehum(dehum_feedback)

    if cs.structs["feature_toggles"]["fan"] == "1":
        if cs.structs["feature_toggles"]["fan_pid"] == "1":
            fan_feedback = int(fan_pid(temperature , humidity, co2,
                                int(cs.structs["device_params"]["target_temperature"]), int(cs.structs["device_params"]["target_humidity"]), int(cs.structs["device_params"]["target_co2"]),
                                last_temperature,last_humidity, last_co2,
                                last_target_temperature,last_target_humidity, last_target_co2,
                                int(cs.structs["device_params"]["Pt_fan"]), int(cs.structs["device_params"]["It_fan"]), int(cs.structs["device_params"]["Dt_fan"]),
                                int(cs.structs["device_params"]["Ph_fan"]), int(cs.structs["device_params"]["Ih_fan"]), int(cs.structs["device_params"]["Dh_fan"]),
                                int(cs.structs["device_params"]["Pc_fan"]), int(cs.structs["device_params"]["Ic_fan"]), int(cs.structs["device_params"]["Dc_fan"])))
        run_fan(fan_feedback)

    if cs.structs["feature_toggles"]["water"] == "1":
        if cs.structs["feature_toggles"]["water_pid"] == "1":
            water_feedback = int(water_pid(substrate_moisture, int(cs.structs["device_params"]["target_substrate_moisture"]),
                                last_substrate_moisture, last_target_substrate_moisture,
                                int(cs.structs["device_params"]["P_moisture"]), int(cs.structs["device_params"]["I_moisture"]), int(cs.structs["device_params"]["D_moisture"])))
        run_water(water_feedback)

    if cs.structs["feature_toggles"]["light"] == "1":
        run_light()

    if cs.structs["feature_toggles"]["air"] == "1":
        run_air()

    if cs.structs["feature_toggles"]["camera"] == "1":
        run_camera()

#unfinished
def controller_log():

    feedback = {}
    timers = {}

    if cs.structs["feature_toggles"]["heater"] == "1":
        if cs.structs["feature_toggles"]["heat_pid"] == "1":
            feedback.update({"Heater Intensity: ": temp_feedback})
        else:
            timers.update({"Heater Duration (seconds run for): ": cs.structs["device_params"]["heater_duration"]})
            timers.update({"Heater Interval (seconds between runs): ": cs.structs["device_params"]["heater_interval"]})
    
    if cs.structs["feature_toggles"]["humidifier"] == "1":
        if cs.structs["feature_toggles"]["heat_pid"] == "1":
            feedback.update({"Humidifier Intensity: ": hum_feedback})
        else:
            timers.update({"Humidifier Duration (seconds run for): ": cs.structs["device_params"]["humidifier_duration"]})
            timers.update({"Humidifier Interval (seconds between runs): ": cs.structs["device_params"]["humidifier_interval"]})
    
    if cs.structs["feature_toggles"]["dehumidifier"] == "1":
        if cs.structs["feature_toggles"]["heat_pid"] == "1":
            feedback.update({"Dehumidifier Intensity: ": dehum_feedback})
        else:
            timers.update({"Dehumidifier Duration (seconds run for): ": cs.structs["device_params"]["dehumidifier_duration"]})
            timers.update({"Dehumidifier Interval (seconds between runs): ": cs.structs["device_params"]["dehumidifier_interval"]})
    
    if cs.structs["feature_toggles"]["fan"] == "1":
        if cs.structs["feature_toggles"]["fan_pid"] == "1":
            feedback.update({"Fan Intensity: ": fan_feedback})
        else:
            timers.update({"Fan Duration (minutes run for): ": cs.structs["device_params"]["fan_duration"]})
            timers.update({"Fan Interval (minutes between runs): ": cs.structs["device_params"]["fan_interval"]})

    if cs.structs["feature_toggles"]["water"] == "1":
        if cs.structs["feature_toggles"]["water_pid"] == "1":
            feedback.update({"Irrigation Intensity: ": water_feedback})
        else:
            timers.update({"Irrigation Duration (seconds run for): ": cs.structs["device_params"]["watering_duration"]})
            timers.update({"Irrigation Interval (hours between runs): ": cs.structs["device_params"]["watering_interval"]})
    
    if cs.structs["feature_toggles"]["air"] == "1":
        timers.update({"Air Pump Turns On at (Hourly Time 0-23): ": cs.structs["device_params"]["time_start_air"]})
        timers.update({"Air Pump Turns Off at (Hourly Time 0-23): ": cs.structs["device_params"]["time_stop_air"]})
        timers.update({"Air Pump Interval (seconds between runs): ": cs.structs["device_params"]["air_interval"]})

    if cs.structs["feature_toggles"]["light"] == "1":
        timers.update({"Light Turns On at (Hourly Time 0-23): ": cs.structs["device_params"]["time_start_light"]})
        timers.update({"Light Turns Off at (Hourly Time 0-23): ": cs.structs["device_params"]["time_stop_light"]})
        timers.update({"Light Interval (seconds between runs): ": cs.structs["device_params"]["air_interval"]})

    if cs.structs["feature_toggles"]["camera"] == "1":
        timers.update({" Duration (seconds run for): ": cs.structs["device_params"]["heater_duration"]})
        if cs.structs["feature_toggles"]["ndvi"] == "1":
            timers.update({"Capture Mode": "NDVI"})
        else:
            timers.update({"Capture Mode": "Raw AWB Imaging"})
        timers.update({"Camera Interval (seconds between image capture): ": cs.structs["hardware_config"]["camera_settings"]["picture_frequency"]})

    if feedback:
        print("Feedback Settings = ")
        pprint.pprint(feedback)
    if timers:
        print("Timer Settings = ")
        pprint.pprint(timers)

def data_out():
    global data_timer
    
    #write data and send to server after set time elapses
    if time.time() - data_timer > 300:

        try:
            cs.load_state()
            payload = cs.structs["sensor_info"]
            timestamp = {"time": str(datetime.datetime.now())}
            payload.update(timestamp)

            if cs.structs["feature_toggles"]["save_data"] == "1":
                #save data to .csv
                print("Writing to csv")
                write_csv('/home/pi/oasis-grow/data_out/sensor_feed/sensor_data.csv', payload)

                if cs.structs["device_state"]["connected"] == "1":
                    #write data to disk and exchange with cloud if connected
                    dbt.patch_firebase_dict(cs.structs["access_config"],payload)

                    #send new time-series to firebase
                    send_csv('/home/pi/oasis-grow/data_out/sensor_feed/sensor_data.csv')

            data_timer = time.time()

        except Exception as e:
            print(err.full_stack())
            data_timer = time.time()

def clean_up_processes():
    global heat_process, humidity_process, dehumidify_process, fan_process, light_process, camera_process, water_process, air_process        

    #clean up all processes
    cs.load_state()

    if (cs.structs["feature_toggles"]["heater"] == "1") and (heat_process != None): #go through toggles and kill active processes
        heat_process.terminate()
        heat_process.wait()

    if (cs.structs["feature_toggles"]["humidifier"] == "1") and (humidity_process != None):
        humidity_process.terminate()
        humidity_process.wait()

    if (cs.structs["feature_toggles"]["dehumidifier"] == "1") and (dehumidify_process != None):
        dehumidify_process.terminate()
        dehumidify_process.wait()

    if (cs.structs["feature_toggles"]["fan"] == "1") and (fan_process != None):
        fan_process.terminate()
        fan_process.wait()

    if (cs.structs["feature_toggles"]["water"] == "1") and (water_process != None):
        water_process.terminate()
        water_process.wait()

    if (cs.structs["feature_toggles"]["light"] == "1") and (light_process != None):
        light_process.terminate()
        light_process.wait()

    if (cs.structs["feature_toggles"]["air"] == "1") and (air_process != None):
        air_process.terminate()
        air_process.wait()

    if (cs.structs["feature_toggles"]["camera"] == "1") and (camera_process != None):
        camera_process.terminate()
        camera_process.wait()

#terminates the program and all running subprocesses
def terminate_program(*args): #Depends on: cs.load_state(), 'sys', 'subprocess' #Modifies: heat_process, humidity_process, fan_process, light_process, camera_process, water_process

    print("Terminating Program...")
    clean_up_processes()

    #flip "running" to 0
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "0", db_writer = dbt.patch_firebase)

    cs.safety.unlock(cs.lock_filepath,resource_name)
    sys.exit()

@err.Error_Handler
def main_setup():
    global data_timer, minion 

    #Load state variables to start the main program
    cs.load_state()

    #exit early if opening subprocess daemon
    if str(sys.argv[1]) == "daemon":
        print("core daemon started")
        #kill the program
        sys.exit()
    if str(sys.argv[1]) == "main":
        print("core main started")
        #log main start
        #flip "running" to 1 to make usable from command line
        if cs.structs["device_state"]["connected"] == 1:
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "1", db_writer = dbt.patch_firebase)
        else:
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "1")
        #continue with program execution
        pass
    else:
        print("please offer valid run parameters")
        sys.exit()

    #attempt to make serial connection but only if there is a sensor active
    if ((cs.structs["feature_toggles"]["temperature_sensor"] == "1") \
                or (cs.structs["feature_toggles"]["humidity_sensor"] == "1") \
                    or (cs.structs["feature_toggles"]["water_level_sensor"] == "1") \
                        or (cs.structs["feature_toggles"]["co2_sensor"] == "1") \
                            or (cs.structs["feature_toggles"]["lux_sensor"] == "1") \
                                or (cs.structs["feature_toggles"]["ph_sensor"] == "1") \
                                    or (cs.structs["feature_toggles"]["tds_sensor"] == "1") \
                                        or (cs.structs["feature_toggles"]["substrate_moisture_sensor"] == "1") \
                                            or (cs.structs["feature_toggles"]["onboard_led"] == "0")):
        minion.start_serial_in()

    #start the clock for timimg .csv writes and data exchanges with server
    data_timer = time.time() - 300

@err.Error_Handler
def main_loop():
    #launch main program loop
    try:
        print("Begin environmental data collection and control")
        print("------------------------------------------------------------")

        while True:
            
            update_derivative_banks() #this occurs in near-realtime, as opposed to storage and exchange every 5 min

            cs.load_state() 

            smart_listener()
            
            run_active_equipment()
            
            controller_log()
            
            data_out()

            time.sleep(5)

    except KeyboardInterrupt:
        print("Core interrupted by user.")
        terminate_program()
    except Exception:
        print("Core encoutered an error!")
        print(err.full_stack())
        terminate_program()

if __name__ == '__main__':
    cs.check_lock(resource_name) #Convention should be to do locks and signal handlers here,
    signal.signal(signal.SIGTERM, terminate_program) #as this is commonly understood as program entry point.
    main_setup()
    main_loop()

#FEATURE EXTRACTION:
#   Almost everything we do here can be put into groups of functionality & extracted into various modules.
#   We want the core to parse configs, load functions for each feature, and interatively run + chain for all enabled
#   The end result should be that it is easier to add a new metrics, data sources, analyses, reaction, and outputs to the core program  
#   An easier option would be to make everything in this file an imported module, and then manually note where each module group touches in the code :)
