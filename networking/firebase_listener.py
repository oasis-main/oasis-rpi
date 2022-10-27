import sys
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

    #checks if file exists and makes a blank one if not
    #the path has to be set for box
    device_state_fields = list(cs.structs["device_state"].keys())
    control_params_fields = list(cs.structs["control_params"].keys())
    hardware_config_groups = list(cs.structs["hardware_config"].keys())

    path = None

    if field in device_state_fields:
        path = "/home/pi/oasis-grow/configs/device_state.json"
    if field in control_params_fields:
        path = "/home/pi/oasis-grow/configs/control_params.json"
    if field in hardware_config_groups:
        path = "/home/pi/oasis-grow/configs/hardware_config.json"

    print(path)
    print(field)
    print(new_data)

    #open data config file
    #edit appropriate spot
    if path is not None:
        
        if path not in hardware_config_groups:
            cs.write_state(path, field, new_data, db_writer = None)
        else:
            group = field #the "field" is actually the root of our nested json
            cs.write_nested_dict(path, field, new_data) #so we pathc that field (nested json group ) with a new data ()

def stream_handler(m):
    #some kind of update
    #might be from start up or might be user changed it
    if m['event']=='put' or m['event']=='patch' or m['event']=='post':
        print(m)
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
        #fetch all the most recent data from the database
        dbt.fetch_device_data(cs.structs["access_config"])
        #actual section that launches the listener
        detect_field_events(user, db)
        
        while True:
            pass #we're going to hang this one infinitely until terminated from above
    
    except SystemExit:
        print("Terminating listener...")
    except KeyboardInterrupt:
        print("Listener was interrupted...")    
    except Exception:
        print(err.full_stack())
        print("Listener encountered an error!")
    finally:
        print("Database listener deactivated.")
        cs.safety.unlock(cs.lock_filepath,resource_name)
        
        