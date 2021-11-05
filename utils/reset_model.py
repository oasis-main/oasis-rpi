import sys
import json
from subprocess import Popen

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

#all functions depend on subprocess module
def reset_device_state():
    reset_d = Popen(["sudo", "cp", "/home/pi/oasis-grow/defaults/device_state_default_template.json", "/home/pi/oasis-grow/configs/device_state.json"])
    reset_d.wait()

def reset_grow_params():
    reset_g = Popen(["sudo", "cp", "/home/pi/oasis-grow/defaults/grow_params_default_template.json", "/home/pi/oasis-grow/configs/grow_params.json"])
    reset_g.wait()
    
def reset_access_config():
    reset_a = Popen(["sudo", "cp", "/home/pi/oasis-grow/defaults/access_config_default_template.json", "/home/pi/oasis-grow/configs/access_config.json"])
    reset_a.wait()

def reset_hardware_config():
    reset_h = Popen(["sudo", "cp", "/home/pi/oasis-grow/defaults/hardware_config_default_template.json", "/home/pi/oasis-grow/configs/hardware_config.json"])
    reset_h.wait()

def reset_feature_toggles():
    reset_f = Popen(["sudo", "cp", "/home/pi/oasis-grow/defaults/feature_toggles_default_template.json", "/home/pi/oasis-grow/configs/feature_toggles.json"])
    reset_f.wait()

def reset_logs():
    reset_l = Popen(["sudo", "cp", "/home/pi/oasis-grow/defaults/grow_ctrl_log_default_template.json", "/home/pi/oasis-grow/data_out/logs/grow_ctrl_log.json"])
    reset_l.wait()
    
def reset_locks():
    reset_lox = Popen(["sudo", "cp", "/home/pi/oasis-grow/defaults/locks_default_template.json", "/home/pi/oasis-grow/configs/locks.json"])
    reset_lox.wait()

def reset_nonhw_configs():
    reset_device_state()
    reset_grow_params()
    reset_access_config()

def reset_data_out():
    clear_image_feed = Popen(["sudo", "rm", "-rf", "/home/pi/oasis-grow/data_out/image_feed"])
    clear_image_feed.wait()
    clear_sensor_feed = Popen(["sudo", "rm", "-rf", "/home/pi/oasis-grow/data_out/sensor_feed"])
    clear_sensor_feed.wait()
    clear_logs = Popen(["sudo", "rm", "-rf", "/home/pi/oasis-grow/data_out/logs"])
    clear_logs.wait()
    clear_dir = Popen(["sudo", "rm", "-rf", "/home/pi/oasis-grow/data_out"])
    clear_dir.wait()
    
    new_dir = Popen(["sudo", "mkdir", "/home/pi/oasis-grow/data_out"])
    new_dir.wait()
    new_image_feed = Popen(["sudo", "mkdir", "/home/pi/oasis-grow/data_out/image_feed"])
    new_image_feed.wait()
    new_sensor_feed = Popen(["sudo", "mkdir", "/home/pi/oasis-grow/data_out/sensor_feed"])
    new_sensor_feed.wait()
    new_logs = Popen(["sudo", "mkdir", "/home/pi/oasis-grow/data_out/logs"])
    new_logs.wait()
    reset_logs()

def reset_image_feed():
    clear_image_feed = Popen(["sudo", "rm", "-rf", "/home/pi/oasis-grow/data_out/image_feed"])
    clear_image_feed.wait()
    new_image_feed = Popen(["sudo", "mkdir", "/home/pi/oasis-grow/data_out/image_feed"])
    new_image_feed.wait()
    
#function that runs all the other functions
def reset_all():
    reset_device_state()
    reset_feature_toggles()
    reset_grow_params()
    reset_access_config()
    reset_hardware_config()
    reset_feature_toggles()
    reset_data_out()

if __name__ == "__main__":
    reset_all()

