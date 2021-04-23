import json
from subprocess import Popen

#all functions depend on subprocess module
def reset_device_state():
    reset_process = Popen(["sudo", "cp", "/home/pi/grow-ctrl/device_state_default_template.json", "/home/pi/device_state.json"])
    reset_process.wait()
    reset_process = Popen(["sudo","cp","/home/pi/grow-ctrl/device_state_default_template.json", "/home/pi/device_state_buffer.json"])
    reset_process.wait()

def reset_grow_params():
    reset_process = Popen(["sudo", "cp", "/home/pi/grow-ctrl/grow_params_default_template.json", "/home/pi/grow_params.json"])
    reset_process.wait()
    reset_process = Popen(["sudo","cp","/home/pi/grow-ctrl/grow_params_default_template.json", "/home/pi/grow_params_buffer.json"])
    reset_process.wait()

def reset_access_config():
    reset_process = Popen(["sudo", "cp", "/home/pi/grow-ctrl/access_config_default_template.json", "/home/pi/access_config.json"])
    reset_process.wait()
    reset_process = Popen(["sudo","cp","/home/pi/grow-ctrl/access_config_default_template.json", "/home/pi/access_config_buffer.json"])
    reset_process.wait()

def reset_hardware_config():
    reset_process = Popen(["sudo", "cp", "/home/pi/grow-ctrl/hardware_config_default_template.json", "/home/pi/hardware_config.json"])
    reset_process.wait()

def reset_feature_toggles():
    reset_process = Popen(["sudo", "cp", "/home/pi/grow-ctrl/feature_toggles_default_template.json", "/home/pi/feature_toggles.json"])
    reset_process.wait()

def reset_logs():
    reset_process = Popen(["sudo", "cp", "/home/pi/grow-ctrl/growCtrl_log_default_template.json", "/home/pi/logs/growCtrl_log.json"])
    reset_process.wait()

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

