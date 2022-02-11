from cgi import test
import os
import os.path
import sys
import subprocess
from subprocess import Popen
import json
import requests
import time

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/home/pi/oasis-grow/imaging')
sys.path.append('/home/pi/oasis-grow/networking')
sys.path.append('/home/pi/oasis-grow/actuators')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

import main
import grow_ctrl
import detect_db_events, oasis_setup
import cameraElement
import update, reset_model, send_image_test

def test_state_handlers():
    
    main.stately.load_state()
    main.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    main.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    grow_ctrl.stately.load_state()
    grow_ctrl.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    grow_ctrl.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    detect_db_events.stately.load_state()
    detect_db_events.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    detect_db_events.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    oasis_setup.stately.load_state()
    oasis_setup.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    oasis_setup.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    cameraElement.stately.load_state()
    cameraElement.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    cameraElement.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    update.stately.load_state()
    update.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    update.stately.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    print("All state handlers working.")

def test_reset_model():
    reset_model.reset_device_state()
    reset_model.reset_grow_params()
    reset_model.reset_locks()
    reset_model.reset_data_out()
    reset_model.reset_image_feed()

    print("Most common reset-model functions operational")

def test_serial_connections():
    main.start_serial()
    print("Main serial is working")

    grow_ctrl.start_serial()
    print("Core serial is working")

def test_listen():
    grow_ctrl.listen()
    print("Listening for data from Arduino")
    print(str(grow_ctrl.temperature))
    print(str(grow_ctrl.humidity))

def test_camera():
    grow_ctrl.run_camera(0)
    print("Is camera working?")

def test_heater():
    grow_ctrl.run_heat(20)
    print("Is heater working?")

def test_humidifier():
    grow_ctrl.run_hum(50)
    print("Is humidifier working?")   
    
def test_dehumidifier():
    grow_ctrl.run_dehum(50)
    print("Is dehumidifier working?")

def test_fan():
    grow_ctrl.run_fan(50)
    print("Is fan working?")
    
def test_light():
    grow_ctrl.run_light(0,0,10)
    print("Is light working?")

def test_water():
    grow_ctrl.run_water(15,0)
    print("Is water working?")

def test_air():
    grow_ctrl.run_air(0,0,10)
    print("Is air working?")
    
def test_save_csv():
    tod = str(time.strftime('%l:%M%p %Z, %b %d %Y'))
    temperature = str(70)
    humidity = str(50)
    water_low = str(0)
    grow_ctrl.write_csv('/home/pi/oasis-grow/data_out/sensor_feed/sensor_data.csv', {"time": tod, "temperature": temperature, "humidity": humidity, "water_low": water_low})
    print("wrote data to csv")

def test_cloud_connection():
    main.connect_firebase()

def test_send_image():
    send_image_test.send_image_test()

def test_update():
    update.get_update_test()
    
def test_AP_up():
    main.enable_AP()

def test_WiFi_setup():
    main.check_AP()

def test_AP_down():
    main.enable_WiFi()

def test_all_components():
    test_state_handlers()
    test_reset_model()
    #test_serial_connections()
    #test_listen()
    test_camera()
    test_heater()
    test_humidifier()
    test_dehumidifier()
    test_fan()
    test_light()
    test_water()
    test_air()
    test_save_csv()
    #test_cloud_connection()
    #test_send_image()
    #test_update()
    

if __name__ == "__main__":
   test_all_components()

