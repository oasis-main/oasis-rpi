import sys
import subprocess
from subprocess import Popen
import json

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

#declare process management variables
ser_in = None
sensor_info = None
heat_process = None
hum_process = None
fan_process = None
light_process = None
camera_process = None
water_process = None

#declare sensor data variables
temp = 0
hum = 0
last_temp = 0
last_hum = 0
last_targetT = 0
last_targetH = 0
waterLow = 0

#loads device state, hardware, and access configurations
def load_state(): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, feature_toggles, access_config, grow_params

    with open("/home/pi/oasis-grow/configs/device_state.json") as d:
        device_state = json.load(d)
    d.close()

    with open("/home/pi/oasis-grow/configs/grow_params.json") as g:
        grow_params = json.load(g)
    g.close()

    with open("/home/pi/oasis-grow/configs/access_config.json") as a:
        access_config = json.load(a)
    a.close()

    with open ("/home/pi/oasis-grow/configs/feature_toggles.json") as f:
        feature_toggles = json.load(f)
    f.close()

def test_serial_connections():
    global ser_in

    try:
        try:
            ser_in = serial.Serial("/dev/ttyUSB0", 9600)
            print("Serial communication with Arduino Nano: Working.")
        except:
            ser_in = serial.Serial("/dev/ttyACM0", 9600)
            print("Serial communication with Arduino Uno: Working.")
    except Exception as e:
        #ser_in = None
        print("Serial connection not working")

def test_camera():
    try:
        camera_process = Popen(['python3', '/home/pi/oasis-grow/imaging/cameraElement.py', "10"]) #If running, then skips. If idle then restarts, If no process, then fails
        print("Camera launched, check to ensure correct behavior")
        camera_process.wait()
    except:
        print("Camera not triggering, there is a problem with the software")

def test_heater():
    try:
        heat_process = Popen(['python3', '/home/pi/oasis-grow/actuators/heatingElement.py', str(100)]) #If running, then skips. If idle then restarts, If no process, then fails
        print("Heat actuator launched, check to ensure correct behavior")
        heat_process.wait()
    except:
        print("Heat actuator not triggering, there is a problem with the software")

def test_humidifier():
    try:
        hum_process = Popen(['python3', '/home/pi/oasis-grow/actuators/humidityElement.py', str(100)]) #If running, then skips. If idle then restarts, If no process, then fails
        print("Humidity actuator launched, check to ensure correct behavior")
        hum_process.wait()
    except:
        print("Humidity actuator not triggering, there is a problem with the software")

def test_fan():
    try:
        fan_process = Popen(['python3', '/home/pi/oasis-grow/actuators/fanElement.py', str(100)]) #If running, then skips. If idle then restarts, If no process, then fails
        print("Fan actuator launched, check to ensure correct behavior")
        fan_process.wait()
    except:
        print("Fan actuator not triggering, there is a problem with the software")

def test_light():
    try:
        light_process = Popen(['python3', '/home/pi/oasis-grow/actuators/lightingElement.py', "0", "0", "10"]) #If running, then skips. If idle then restarts, If no process, then fails
        print("Lighting actuator launched, check to ensure correct behavior")
        light_process.wait()
    except:
        print("Lighting actuator not triggering, there is a problem with the software")

def test_water():
    try:
        water_process = Popen(['python3', '/home/pi/oasis-grow/actuators/wateringElement.py', "10", "0"]) #If running, then skips. If idle then restarts, If no process, then fails
        print("Water actuator launched, check to ensure correct behavior")
        water_process.wait()
    except:
        print("Water actuator not triggering, there is a problem with the software")

def test_air():
    try:
        air_process = Popen(['python3', '/home/pi/oasis-grow/actuators/airElement.py', "0", "0", "10"]) #If running, then skips. If idle then restarts, If no process, then fails
        print("Air actuator launched, check to ensure correct behavior")
        water_process.wait()
    except:
        print("Air actuator not triggering, there is a problem with the software")

def test_cloud_connection():
    load_state()
    print("Testing firebase connection")
    try:
        dict = {"connected": device_state["connected"]}
        data = json.dumps(dict)
        url = "https://oasis-1757f.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
        result = requests.patch(url,data)
        print("Firebase connection working")
    except:
        print("Firebase connection not working")

def run_all_tests():
    test_serial_connections()
    test_camera()
    test_heater()
    test_humidifier()
    test_fan()
    test_light()
    test_water()
    test_air()
    test_cloud_connection()

if __name__ == "__main__":
   load_state()
   run_all_tests()
