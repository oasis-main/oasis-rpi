import sys
import time
import signal

#set custom module path
sys.path.append('/home/pi/oasis-grow')

from utils import concurrent_state as cs
from networking import db_tools as dbt
from utils import error_handler as err

resource_name = "listener"

#sync local configuration with 
def sync_state():
    cloud_data = dbt.fetch_device_data()
    for key_value_pair in list(cloud_data.items()):
        if key_value_pair[0] in list(cs.structs["device_state"].keys()):
            #print("Updating device_state")
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json", key_value_pair[0], key_value_pair[1], db_writer = None)
        elif key_value_pair[0] in list(cs.structs["control_params"].keys()):
            #print("Updating control_params")
            cs.write_state("/home/pi/oasis-grow/configs/control_params.json", key_value_pair[0], key_value_pair[1], db_writer = None)    
        else:
            #print("Not working")
            pass

#make change to config file
def act_on_event(field, new_data):
    #get data and field info
    device_state_fields = list(cs.structs["device_state"].keys())
    control_params_fields = list(cs.structs["control_params"].keys())
    hardware_config_groups = list(cs.structs["hardware_config"].keys())

    config_path = None

    if field in device_state_fields:
        config_path = "/home/pi/oasis-grow/configs/device_state.json"
    elif field in control_params_fields:
        config_path = "/home/pi/oasis-grow/configs/control_params.json"
    elif field in hardware_config_groups:
        config_path = "/home/pi/oasis-grow/configs/hardware_config.json"

    debug_act = True
    
    if debug_act:
        print("Config filepath:")
        print(config_path)
        
        print("Config struct field:")
        print(field)

        print("New Data:")
        print(new_data)

    #open data config file
    #edit appropriate spot
    if config_path is not None: #these are writes made directly to firebase as the admin
        
        if field in (control_params_fields+device_state_fields) & (field != "connected"):
            cs.write_state(config_path, field, new_data, db_writer = None)
        elif field in hardware_config_groups:
            group = field #the "field" is actually the root of our nested json
            json = new_data
            cs.write_nested_dict(config_path, group, json, db_writer = None) #so we path that field (nested json group ) with a new data ()
        else:
            pass
    
    else: #the following are writes made to the database by the dashboard
        
        key = list(new_data.keys())[0]
        val = list(new_data.values())[0]

        if key in device_state_fields:
            config_path = "/home/pi/oasis-grow/configs/device_state.json"
        elif key in control_params_fields:
            config_path = "/home/pi/oasis-grow/configs/control_params.json"
        elif key in hardware_config_groups:
            config_path = "/home/pi/oasis-grow/configs/hardware_config.json"

        if key in (control_params_fields+device_state_fields) & (key != "connected"):
            cs.write_state(config_path, key, val, db_writer = None)
        elif key in hardware_config_groups:
            group = key #the "field" is actually the root of our nested json
            json = val
            cs.write_nested_dict(config_path, group, json, db_writer = None) #so we path that field (nested json group ) with a new data ()
        else:
            return


def stream_handler(m):
    #some kind of update
    #might be from start up or might be user changed it
    if m['event']=='put' or m['event']=='patch' or m['event']=='post':
        print(m) #raw event streaming data coming from firebase
        path = m['path']
        key = path[1:len(path)]
        value = m['data']
        act_on_event(key, value)

    #something else
    else:
        #if this happens... theres a problem...
        #should be handled for
        print('something wierd...', m['event'])
        pass

@err.Error_Handler
def detect_field_events(user, db):
    my_stream = db.child(user['userId']+'/'+cs.structs["access_config"]["device_name"]+"/").stream(stream_handler, user['idToken'])

if __name__ == "__main__":
    cs.check_lock(resource_name)
    signal.signal(signal.SIGTERM, cs.wrapped_sys_exit)
    print("Database listener activated.")
    try:
        cs.load_state()
        user, db, storage = dbt.initialize_user(cs.structs["access_config"]["refresh_token"])
        
        #fetch all the most recent data from the database & patch the listener
        cloud_device = dbt.fetch_device_data(cs.structs["access_config"])
        
        device_state_fields = list(cs.structs["device_state"].keys())
        control_params_fields = list(cs.structs["control_params"].keys())
        hardware_config_groups = list(cs.structs["hardware_config"].keys())

        for k,v in cloud_device.items():
            print("Startup: writing " + str(v) + " to " + str(k))
            if k in device_state_fields:
                start_path = "/home/pi/oasis-grow/configs/device_state.json"
            elif k in control_params_fields:
                start_path = "/home/pi/oasis-grow/configs/control_params.json"
            elif k in hardware_config_groups:
                start_path = "/home/pi/oasis-grow/configs/hardware_config.json"

            if k in (device_state_fields+control_params_fields) & (k != "connected"):
                cs.write_state(start_path, k, v, db_writer = None)
            elif k in hardware_config_groups:
                cs.write_nested_dict(start_path, k, v, db_writer = None) #so we path that field (nested json group ) with a new data ()
            else:
                pass

            time.sleep(0.1)

        #ok, now that we got the startup values...
        #actual section that launches the listener
        detect_field_events(user, db)
        
        while True:
            print("Listener is active...")
            time.sleep(1)
            #we're going to hang this one infinitely until terminated from above
    
    except SystemExit:
        print("Terminating listener...")
    except KeyboardInterrupt:
        print("Listener was interrupted...")    
    except Exception:
        print(err.full_stack())
        print("Listener encountered an error!")
    finally:
        print("Database listener deactivated.")
        cs.rusty_pipes.unlock(cs.lock_filepath, resource_name)
        
        