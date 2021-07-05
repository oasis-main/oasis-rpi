import sys
import json
from subprocess import Popen

#set proper path for modules
sys.path.append("home/pi/.local/lib/python3.9/site-packages")

#all functions depend on subprocess module
def reset_device_state():
    reset_d = Popen(["sudo", "cp", "/home/pi/oasis-grow/device_state_default_template.json", "/home/pi/device_state.json"])
    reset_d.wait()
    reset_d_buff = Popen(["sudo","cp","/home/pi/oasis-grow/device_state_default_template.json", "/home/pi/device_state_buffer.json"])
    reset_d_buff.wait()

def reset_grow_params():
    reset_g = Popen(["sudo", "cp", "/home/pi/oasis-grow/grow_params_default_template.json", "/home/pi/grow_params.json"])
    reset_g.wait()
    reset_g_buff = Popen(["sudo","cp","/home/pi/oasis-grow/grow_params_default_template.json", "/home/pi/grow_params_buffer.json"])
    reset_g_buff.wait()

def reset_access_config():
    reset_a = Popen(["sudo", "cp", "/home/pi/oasis-grow/access_config_default_template.json", "/home/pi/access_config.json"])
    reset_a.wait()
    reset_a_buff = Popen(["sudo","cp","/home/pi/oasis-grow/access_config_default_template.json", "/home/pi/access_config_buffer.json"])
    reset_a_buff.wait()

def reset_hardware_config():
    reset_h = Popen(["sudo", "cp", "/home/pi/oasis-grow/hardware_config_default_template.json", "/home/pi/hardware_config.json"])
    reset_h.wait()

def reset_feature_toggles():
    reset_f = Popen(["sudo", "cp", "/home/pi/oasis-grow/feature_toggles_default_template.json", "/home/pi/feature_toggles.json"])
    reset_f.wait()

def reset_logs():
    reset_l = Popen(["sudo", "cp", "/home/pi/oasis-grow/growCtrl_log_default_template.json", "/home/pi/logs/growCtrl_log.json"])
    reset_l.wait()

def reset_nonhw_configs():
    reset_device_state()
    reset_grow_params()
    reset_access_config()

def reset_data_out():
    clear_image_feed = Popen(["sudo", "rm", "-rf", "/home/pi/data_output/image_feed"])
    clear_image_feed.wait()
    clear_sensor_feed = Popen(["sudo", "rm", "-rf", "/home/pi/data_output/sensor_feed"])
    clear_sensor_feed.wait()
    new_image_feed =  Popen(["sudo", "mkdir", "/home/pi/data_output/image_feed"])
    new_image_feed.wait()
    new_sensor_feed = Popen(["sudo", "mkdir", "/home/pi/data_output/sensor_feed"])
    new_sensor_feed.wait()

#function that runs all the other functions
def reset_all():
    reset_device_state()
    reset_feature_toggles()
    reset_grow_params()
    reset_access_config()
    reset_hardware_config()
    reset_feature_toggles()
    reset_logs()

if __name__ == "__main__":
    reset_device_state()

