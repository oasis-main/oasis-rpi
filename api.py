#import shell modules
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

import concurrent_state as cs
import reset_model as r

def start_core():
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1")
    print("Started system core.")
    return

def stop_core():
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")
    print("Stopped system core.")
    return

def set_temperature_target(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "target_temperature", str(value))
    print("Temperature target was set to: " + str(value) + " degrees farenheit.")
    return

def set_humidity_target(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "target_humidity", str(value))
    print("Relative humidity target was set to: " + str(value) + " percent.")
    return

def set_light_timer(time_start_light, time_start_dark, lighting_interval):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "time_start_light", str(time_start_light))
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "time_start_dark", str(time_start_dark))
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "lighting_interval", str(lighting_interval))
    print("Lights will turn on at " + str(time_start_light) + ":00.")
    print("Lights will turn off at " + str(time_start_dark) + ":00.")
    print("Lights will refresh every " + str(lighting_interval) + " seconds.")
    return

def set_camera_interval(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "camera_interval", str(value))
    print("Camera will take a picture every " + str(value) + " seconds.")
    return

def set_watering_cycle(watering_duration, watering_interval):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "watering_duration", str(watering_duration))
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "watering_interval", str(watering_interval))
    print("Watering pump will run for " + str(watering_duration) + " seconds, once every " + str(watering_interval) + " hours.")
    return

def set_air_timer(time_start_air,time_stop_air, air_interval):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "", str(time_start_air))
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "", str(time_stop_air))
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "", str(air_interval))
    print("Air pump will turn on at " + str(time_start_air) + ":00.")
    print("Air pump will turn off at " + str(time_stop_air) + ":00.")
    print("Air pump will refresh every " + str(air_interval) + " seconds.")
    return

def read_temperature():
    cs.load_state()
    temperature = cs.device_state["temperature"]
    return temperature

def read_humidity():
    cs.load_state()
    humidity = cs.device_state["humidity"]
    return humidity
    
def read_water_level():
    cs.load_state()
    water_low = cs.device_state["water_low"]
    return water_low


def set_heater_response(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "P_temp", str(value))
    print("Heater response gain set to: " + str(value))
    return

def set_heater_damping(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "D_temp", str(value))
    print("Heater damping gain set to: " + str(value))
    return

def set_humidifier_response(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "P_hum", str(value))
    print("Humidifier response gain set to: " + str(value))
    return

def set_humidifier_damping(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "D_hum", str(value))
    print("Humidifier damping gain set to: " + str(value))
    return

def set_fan_response_temp(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "Pt_fan", str(value))
    print("Fan temperature response gain set to: " + str(value))
    return    

def set_fan_damping_temp(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "Dt_fan", str(value))
    print("Fan temperature damping gain set to: " + str(value))
    return

def set_fan_response_hum(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "Ph_fan", str(value))
    print("Fan humidity response gain set to: " + str(value))
    return

def set_fan_damping_temp(value):
    cs.write_state("/home/pi/oasis-grow/configs/grow_params.json", "Dh_fan", str(value))
    print("Fan humidity response gain set to: " + str(value))
    return

def show_state():
    cs.load_state()
    print(cs.device_state)
    return

def show_parameters():
    cs.load_state()
    print(cs.grow_params)
    return

def show_active_features():
    cs.load_state()
    print(cs.feature_toggles)
    return

def show_hardware_pins():
    cs.load_state()
    print(cs.hardware_config)
    return

def reset_state():
    r.reset_device_state()
    return

def reset_parameters():
    r.reset_grow_params()
    return

def reset_creds():
    r.reset_access_config()
    return

def reset_hardware():
    r.reset_hardware_config()
    return

def reset_features():
    r.reset_feature_toggles()
    returnpy

def reset_data_out():
    r.reset_data_out()

def reset_all():
    r.reset_all()
    return