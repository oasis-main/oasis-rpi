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

def update_synced_fields():
    cloud_device = dbt.fetch_device_data(cs.structs["access_config"])

    device_state_fields = list(cs.structs["device_state"].keys())
    control_params_fields = list(cs.structs["control_params"].keys())
    hardware_config_groups = list(cs.structs["hardware_config"].keys())

    #loop through all device data
    for k,v in cloud_device.items():
        print("Listener: writing " + str(v) + " to " + str(k))
        
        #get path for each key we decide should be litened to
        if k in device_state_fields:
            start_path = "/home/pi/oasis-grow/configs/device_state.json"
        elif k in control_params_fields:
            start_path = "/home/pi/oasis-grow/configs/control_params.json"
        elif k in hardware_config_groups:
            start_path = "/home/pi/oasis-grow/configs/hardware_config.json"
        else:
            continue

        if (k in (device_state_fields+control_params_fields)) & (k != "connected"):
            cs.write_state(start_path, k, v, db_writer = None)
        elif k in hardware_config_groups:
            cs.write_nested_dict(start_path, k, v, db_writer = None) #so we path that field (nested json group ) with a new data ()
        else:
            continue

        time.sleep(0.1)

    print("Synced state with cloud")

if __name__ == "__main__":
    cs.check_lock(resource_name)
    signal.signal(signal.SIGTERM, cs.wrapped_sys_exit)
    print("Database listener activated.")
    try:
        cs.load_state()
        #sign the user in
        user, db, storage = dbt.initialize_user(cs.structs["access_config"]["refresh_token"])
        #fetch all the most recent data from the database & patch the listener
        
        listener_timer = time.time()-30
        
        while True:
            if (time.time() - listener_timer) > 30:
                update_synced_fields()
            else:
                time.sleep(1)
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
        
        