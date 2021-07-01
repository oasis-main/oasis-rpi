#import modules
import os
import os.path
import sys
import json
import requests
from subprocess import Popen

#set proper path for modules

#pull repository
changedir = Popen("cd ~/grow-ctrl", shell = True)
changedir.wait()

rmpycache = Popen("sudo rm -rf __pycache__", shell = True)
rmpycache.wait()

gitstash = Popen("git stash", shell = True)
gitstash.wait()

gitpull = Popen("git pull", shell = True)
gitpull.wait()

print("Pulled most recent production repo")

#save existing data into temps, copy new config formats
savehardware = Popen("cp /home/pi/hardware_config.json /home/pi/hardware_config_temp.json", shell = True)
savehardware.wait()

saveaccess = Popen("cp /home/pi/access_config.json /home/pi/access_config_temp.json", shell = True)
saveaccess.wait()

savestate = Popen("cp /home/pi/device_state.json /home/pi/device_state_temp.json", shell = True)
savestate.wait()

saveparams = Popen("cp /home/pi/grow_params.json /home/pi/grow_params_temp.json", shell = True)
saveparams.wait()

savelog = Popen("cp /home/pi/logs/growCtrl_log.json /home/pi/logs/growCtrl_log_temp.json", shell = True)
savelog.wait()

newhardware = Popen("cp hardware_config_default_template.json /home/pi/hardware_config.json", shell = True)
newhardware.wait()

newaccess = Popen("cp access_config_default_template.json /home/pi/access_config.json", shell = True)
newaccess.wait()

newstate = Popen("cp device_state_default.json /home/pi/device_state.json", shell = True)
newstate.wait()

newparams = Popen("cp grow_params_default_template.json /home/pi/grow_params.json", shell = True)
newparams.wait()

newlogs = Popen("cp growCtrl_log_default.json /home/pi/logs/growCtrl_log.json", shell = True)
newlogs.wait()

#preserve existing configs if fields remain the same
#HARDWARE
with open('/home/pi/hardware_config.json') as h: #get new format
    hardware_config = json.load(h)
h.close()

with open('/home/pi/hardware_config_temp.json') as h_temp: #get old data
    hardware_config_temp = json.load(h_temp)
h_temp.close()

#persist old data into new format
old_data_keys = list(hardware_config_temp.keys())
new_format_keys = list(hardware_config.keys())
common_keys = set(old_data_keys) & set(new_format_keys) #common ones between them
#loop through common keys, change values to temp
for key in common_keys:
    hardware_config[key] = hardware_config_temp[key]

with open("/home/pi/hardware_config.json", "r+") as h: #write data to config
        h.seek(0)
        json.dump(hardware_config, h)
        h.truncate()
h.close()

removehwtemp = Popen("sudo rm ~/hardware_config_temp.json", shell = True)
removehwtemp.wait()

#ACCESS
with open('/home/pi/access_config.json') as a: #get new format
    access_config = json.load(a)
a.close()

with open('/home/pi/access_config_temp.json') as a_temp: #get old data
    access_config_temp = json.load(a_temp)
a_temp.close()

#persist old data into new format
old_data_keys = list(access_config_temp.keys())
new_format_keys = list(access_config.keys())
common_keys = set(old_data_keys) & set(new_format_keys) #common ones between them
#loop through common keys, change values to temp
for key in common_keys:
    access_config[key] = access_config_temp[key]

with open("/home/pi/access_config.json", "r+") as a: #write data to config
        a.seek(0)
        json.dump(access_config, a)
        a.truncate()
a.close()

removeatemp = Popen("sudo rm ~/access_config_temp.json", shell = True)
removeatemp.wait()

#DEVICE STATE
with open('/home/pi/device_state.json') as d: #get new format
    device_state = json.load(d)
d.close()

with open('/home/pi/device_state_temp.json') as d_temp: #get old data
    device_state_temp = json.load(d_temp)
d_temp.close()

#persist old data into new format
old_data_keys = list(device_state_temp.keys())
new_format_keys = list(device_state.keys())
common_keys = set(old_data_keys) & set(new_format_keys) #common ones between them
#loop through common keys, change values to temp
for key in common_keys:
    device_state[key] = device_state[key]

with open("/home/pi/device_state.json", "r+") as d: #write data to config
        d.seek(0)
        json.dump(device_state, d)
        d.truncate()
d.close()

removestemp = Popen("sudo rm ~/device_state_temp.json", shell = True)
removestemp.wait()

#GROW PARAMS
with open('/home/pi/grow_params.json') as g: #get new format
    grow_params = json.load(g)
g.close()

with open('/home/pi/grow_params_temp.json') as g_temp: #get old data
    grow_params_temp = json.load(g_temp)
g_temp.close()

#persist old data into new format
old_data_keys = list(grow_params_temp.keys())
new_format_keys = list(grow_params.keys())
common_keys = set(old_data_keys) & set(new_format_keys) #common ones between them
#loop through common keys, change values to temp
for key in common_keys:
    grow_params[key] = grow_params[key]

with open("/home/pi/grow_params.json", "r+") as g: #write data to config
        g.seek(0)
        json.dump(grow_params, g)
        g.truncate()
g.close()

removeptemp = Popen("sudo rm ~/grow_params_temp.json", shell = True)
removeptemp.wait()

#GROW CTRL LOGS
with open('/home/pi/logs/growCtrl_log.json') as l: #get new format
    growCtrl_log = json.load(l)
l.close()

with open('/home/pi/logs/growCtrl_log_temp.json') as l_temp: #get old data
    growCtrl_log_temp = json.load(l_temp)
l_temp.close()

#persist old data into new format
old_data_keys = list(growCtrl_log_temp.keys())
new_format_keys = list(growCtrl_log.keys())
common_keys = set(old_data_keys) & set(new_format_keys) #common ones between them
#loop through common keys, change values to temp
for key in common_keys:
    growCtrl_log[key] = growCtrl_log[key]

with open("/home/pi/logs/growCtrl_log.json", "r+") as l: #write data to config
        l.seek(0)
        json.dump(growCtrl_log, l)
        l.truncate()
l.close()

removeltemp = Popen("sudo rm ~/logs/growCtrl_log_temp.json", shell=True)
removeltemp.wait()

#run external update commands
update_commands = Popen('sudo python3 /home/pi/grow-ctrl/update_commands.py', shell=True)
output, error = update_commands.communicate()


#load local_id & id_token
with open('/home/pi/access_config.json', "r+") as a:
  access_config = json.load(a)
  id_token = access_config['id_token']
  local_id = access_config['local_id']
a.close()

#change awaiting_update to "O", needs editing, also used in grow-ctrl
#url = "https://oasis-1757f.firebaseio.com/"+str(local_id)+".json?auth="+str(id_token)
#data = json.dumps({dict})
#result = requests.patch(url,data)
#print(result)

#reboot
reboot = Popen("sudo reboot", shell = True)
reboot.wait()
