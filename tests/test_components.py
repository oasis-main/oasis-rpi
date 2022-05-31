
import sys

from tests import test_cloud_connection

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/home/pi/oasis-grow/imaging')
sys.path.append('/home/pi/oasis-grow/networking')
sys.path.append('/home/pi/oasis-grow/equipment')

#import and test everything
import main
import api
from core import core
from networking import connect_oasis, detect_db_events
from imaging import camera
from utils import update, reset_model

import time

def test_state_handlers():
    print("Testing state handlers...")
    main.cs.load_state()
    main.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    main.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    core.cs.load_state()
    core.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    core.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    detect_db_events.cs.load_state()
    detect_db_events.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    detect_db_events.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    connect_oasis.cs.load_state()
    connect_oasis.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    connect_oasis.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    camera.cs.load_state()
    camera.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    camera.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    update.cs.load_state()
    update.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("1"))
    update.cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "running", str("0"))

    print("All state handlers working.")

def test_reset_model():
    print("Testing reset model functions...")
    reset_model.reset_all()
    print("Reset-model functions operational")

def test_serial_connections():
    print("Testing serial minions...")
    main.minion.start_serial_in()
    print("Main serial is working")

    core.minion.start_serial_out()
    print("Core serial is working")

def test_listen():
    print("Testing listener...")
    core.smart_listener()
    print("Listening for data from Arduino")
    print(str(core.sensor_info))

def test_save_csv():
    print("Testing csv writer...")
    tod = str(time.strftime('%l:%M%p %Z, %b %d %Y'))
    temperature = str(70)
    humidity = str(50)
    water_low = str(0)
    core.write_csv('/home/pi/oasis-grow/data_out/sensor_feed/sensor_data.csv', {"time": tod, "temperature": temperature, "humidity": humidity, "water_low": water_low})
    reset_model.reset_data_out()
    print("wrote data to csv")

def test_camera():
    print("Testing camera...")
    core.run_camera(0)
    print("Is camera working?")

def test_heater():
    print("Testing heater...")
    core.run_heat(20)
    print("Is heater working?")

def test_humidifier():
    print("Testing humidifier...")
    core.run_hum(50)
    print("Is humidifier working?")   
    
def test_dehumidifier():
    print("Testing dehumidifier...")
    core.run_dehum(50)
    print("Is dehumidifier working?")

def test_fan():
    print("Testing fan...")
    core.run_fan(50)
    print("Is fan working?")
    
def test_light():
    print("Testing light...")
    core.run_light(0,0,10)
    print("Is light working?")

def test_water():
    print("Testing water...")
    core.run_water(15,0)
    print("Is water working?")

def test_air():
    print("Testing air...")
    core.run_air(0,0,10)
    print("Is air working?")

def test_core(interval):
    print("Testing core...")
    api.start_core()
    time.sleep(int(interval))
    api.stop_core()
    
if __name__ == "__main__":
   test_state_handlers()
   test_reset_model()
   test_serial_connections()
   test_listen()
   test_save_csv()
   test_camera()
   test_heater()
   test_humidifier()
   test_dehumidifier()
   test_fan()
   test_light()
   test_water()
   test_air()
   test_core()

