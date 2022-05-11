#import modules
import os
import os.path
import sys
import json
import requests
from subprocess import Popen

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

import reset_model
import concurrent_state as cs

#get latest code from designated repository
def git_pull():
    gitpull = Popen(["git", "pull"]) #should be whatever branch the code was installed from
    gitpull.wait()

    print("Pulled most recent code changes from repository.")

#save existing data into temps
def save_old_configs():
    savefeatures = Popen(["cp", "/home/pi/oasis-grow/configs/feature_toggles.json", "/home/pi/oasis-grow/configs/feature_toggles_temp.json"])
    savefeatures.wait()
    
    savehardware = Popen(["cp", "/home/pi/oasis-grow/configs/hardware_config.json", "/home/pi/oasis-grow/configs/hardware_config_temp.json"])
    savehardware.wait()

    saveaccess = Popen(["cp", "/home/pi/oasis-grow/configs/access_config.json", "/home/pi/oasis-grow/configs/access_config_temp.json"])
    saveaccess.wait()

    savestate = Popen(["cp", "/home/pi/oasis-grow/configs/device_state.json", "/home/pi/oasis-grow/configs/device_state_temp.json"])
    savestate.wait()

    saveparams = Popen(["cp", "/home/pi/oasis-grow/configs/device_params.json", "/home/pi/oasis-grow/configs/device_params_temp.json"])
    saveparams.wait()

    print("Saved existing configs to temporary files")

#transfer compatible configs which we save before getting the new code and default files
def transfer_compatible_configs(config_path,temp_config_path):

    with open(config_path) as x: #get new format
        config = json.load(x)

    with open(temp_config_path) as x_temp: #get old data
        config_temp = json.load(x_temp)

    #persist old data into new format
    old_data_keys = list(config_temp.keys())
    new_format_keys = list(config.keys())
    common_keys = set(old_data_keys) & set(new_format_keys) #common ones between them

    #loop through common keys, change values to temp
    for key in common_keys:
        config[key] = config_temp[key]

    with open(config_path, "r+") as x: #write data to config
        x.seek(0)
        json.dump(config, x)
        x.truncate()

    remove_temp = Popen(["rm", temp_config_path])
    remove_temp.wait()

def get_update(test=False):
    #get latest code
    git_pull()

    #back up the configs & state that can survive update
    save_old_configs()
    reset_model.reset_all()
    transfer_compatible_configs('/home/pi/oasis-grow/configs/feature_toggles.json', '/home/pi/oasis-grow/configs/feature_toggles_temp.json')
    transfer_compatible_configs('/home/pi/oasis-grow/configs/hardware_config.json', '/home/pi/oasis-grow/configs/hardware_config_temp.json')
    transfer_compatible_configs('/home/pi/oasis-grow/configs/access_config.json', '/home/pi/oasis-grow/configs/access_config_temp.json')
    transfer_compatible_configs('/home/pi/oasis-grow/configs/device_state.json', '/home/pi/oasis-grow/configs/device_state_temp.json')
    transfer_compatible_configs('/home/pi/oasis-grow/configs/device_params.json', '/home/pi/oasis-grow/configs/device_params_temp.json')
    print("Transfered compatible state & configs, removing temporary files")

    #run external update commands
    sh_stage = Popen(["sudo", "chmod" ,"+x", "/home/pi/oasis-grow/scripts/update_patch.sh"])
    output, error = sh_stage.communicate()

    sh_patch = Popen(["sudo", "/home/pi/oasis-grow/scripts/update_patch.sh"])
    output, error = sh_patch.communicate()

    #load state to get configs & state
    cs.load_state()

    #change awaiting_update to "O" in firebase and locally
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "awaiting_update", "0")

    if not test:
        #reboot
        print("Rebooting...")
        reboot = Popen(["sudo","systemctl","reboot"])
        reboot.wait()

if __name__ == '__main__':
    get_update()