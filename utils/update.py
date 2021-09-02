#import modules
import os
import os.path
import sys
import json
import requests
from subprocess import Popen
import reset_model

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

device_state = None
grow_params = None
hardware_config = None
access_config = None

#loads device state, grow_params, hardware, and access configurations
def load_state_main(): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, grow_params, hardware_config, access_config

    with open("/home/pi/oasis-grow/configs/device_state.json") as d:
        device_state = json.load(d) #get device state

    with open("/home/pi/oasis-grow/configs/grow_params.json") as g:
        grow_params = json.load(g) #get device state

    with open("/home/pi/oasis-grow/configs/hardware_config.json") as h:
        hardware_config = json.load(h) #get hardware state

    with open("/home/pi/oasis-grow/configs/access_config.json") as a:
        access_config = json.load(a) #get access state
    #print("Loaded state")

#modifies a firebase variable
def patch_firebase(field,value): #Depends on: load_state_main(),'requests','json'; Modifies: database['field'], state variables
    data = json.dumps({field: value})
    url = "https://oasis-1757f.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)
    print("Updated firebase")

#save key values to .json
def write_state(path,field,value): #Depends on: load_state_main(), patch_firebase, 'json'; Modifies: path
    load_state_main() #get connection status

    #these will be loaded in by the listener, so best to make sure we represent the change in firebase too
    if device_state["connected"] == "1": #write state to cloud
        try:
            patch_firebase(field,value)
        except:
            pass

    with open(path, "r+") as x: #write state to local files
        data = json.load(x)
        data[field] = value
        x.seek(0)
        json.dump(data, x)
        x.truncate()
    print("Wrote local state")

#get latest code from designated repository
def git_pull():
    gitpull = Popen(["git", "pull"])
    gitpull.wait()

    print("Pulled most recent production repo")

#save existing data into temps
def save_old_configs():
    savehardware = Popen(["cp", "/home/pi/oasis-grow/configs/hardware_config.json", "/home/pi/oasis-grow/configs/hardware_config_temp.json"])
    savehardware.wait()

    saveaccess = Popen(["cp", "/home/pi/oasis-grow/configs/access_config.json", "/home/pi/oasis-grow/configs/access_config_temp.json"])
    saveaccess.wait()

    savestate = Popen(["cp", "/home/pi/oasis-grow/configs/device_state.json", "/home/pi/oasis-grow/configs/device_state_temp.json"])
    savestate.wait()

    saveparams = Popen(["cp", "/home/pi/oasis-grow/configs/grow_params.json", "/home/pi/oasis-grow/configs/grow_params_temp.json"])
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

    remove_temp = Popen(["sudo", "rm", temp_config_path])
    remove_temp.wait()

if __name__ == '__main__':

    #get latest code
    git_pull()

    #back up the configs & state that can survive update
    save_old_configs()
    reset_model.reset_all()
    transfer_compatible_configs('/home/pi/oasis-grow/configs/hardware_config.json', '/home/pi/oasis-grow/configs/hardware_config_temp.json')
    transfer_compatible_configs('/home/pi/oasis-grow/configs/access_config.json', '/home/pi/oasis-grow/configs/access_config_temp.json')
    transfer_compatible_configs('/home/pi/oasis-grow/configs/device_state.json', '/home/pi/oasis-grow/configs/device_state_temp.json')
    transfer_compatible_configs('/home/pi/oasis-grow/configs/grow_params.json', '/home/pi/oasis-grow/configs/grow_params_temp.json')
    print("Transfered compatible state & configs, removing temporary files")

    #run external update commands
    update_commands = Popen(["sudo", "python3", "/home/pi/oasis-grow/utils/update_commands.py"])
    output, error = update_commands.communicate()

    #load state to get configs & state for conn
    load_state_main()

    #change awaiting_update to "O" in firebase and locally
    write_state("/home/pi/oasis-grow/configs/device_state.json", "awaiting_update", "0")

    #reboot
    print("Rebooting...")
    reboot = Popen(["sudo","reboot"])
    reboot.wait()
