#import shell modules
import sys

#set custom module path
sys.path.append('/home/pi/oasis-grow')

#concurrency
import rusty_pipes
from utils import concurrent_state as cs

#networking
from networking import db_tools as dbt

#housekeeping
from utils import error_handler as err
from utils import reset_model

#check if the device is waiting to be added to firebase, if it is then add it, otherwise skip
def add_new_device():
    cs.load_state()

    #assemble data to initialize firebase
    setup_dict = {} #Access & hardware config will be kept private, not shared with cloud 
    setup_dict.update(cs.structs["device_state"])
    setup_dict.update(cs.structs["device_params"])
    setup_dict.update(cs.structs["feature_toggles"])
    setup_dict.update(cs.structs["sensor_info"])
    setup_dict_named = {cs.structs["access_config"]["device_name"] : setup_dict}
    my_data = setup_dict_named
    #print(my_data)
    #print(type(my_data))

    #add box data to firebase (replace with send_dict)
    patch_request = dbt.firebase_add_device(cs.structs["access_config"],my_data)
    
    if patch_request.ok:
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","new_device","0", db_writer = dbt.patch_firebase)
        print("New device added to firebase")
    else:
        print("Failed to add new device")

#deletes a box if the cloud is indicating that it should do so
def delete_device():    
    print("Removing device from Oasis Network...")
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase) #make sure it doesn't write anything to the cloud

    print("Database monitoring deactivated")
    reset_model.reset_nonhw_configs()
    
    print("Device has been reset to default configuration")
    systemctl_reboot = rusty_pipes.Open(["sudo", "systemctl", "reboot"])
    systemctl_reboot.wait()

#connects system to firebase
def connect_to_firebase(): #depends on: cs.load_state(), cs.write_state(), dbt.patch_firebase(), 'requests'; Modifies: access_config.json, device_state.json
    
    #load state so we can use access credentials
    cs.load_state()
    wak = cs.structs["access_config"]["wak"]
    email = cs.structs["access_config"]["e"]
    password = cs.structs["access_config"]["p"]

    print("Checking for connection...")

    try:
        print("FireBase verification:")

        #fetch refresh token
        refresh_token = dbt.get_refresh_token(wak, email, password)
        #fetch refresh token and save to access_config
        cs.write_state("/home/pi/oasis-grow/configs/access_config.json","refresh_token", refresh_token, db_writer = None)

        #bring in the refresh token for use further down
        cs.load_state()
        refresh_token = cs.structs["access_config"]["refresh_token"]
        print("Obtained a refresh token!")

        #fetch a new id_token & local_id
        id_token, user_id = dbt.get_local_credentials(wak, refresh_token)
        #write local credentials to access config
        cs.write_state("/home/pi/oasis-grow/configs/access_config.json","id_token", id_token, db_writer = None)
        cs.write_state("/home/pi/oasis-grow/configs/access_config.json","local_id", user_id, db_writer = None)
        print("Devie authorized with local credentials.")

        #launch new_device check at network startup
        cs.check_state("new_device", add_new_device)

        #start listener to bring in db changes on startup
        #Main setup always sets 'connected' == "0"
        dbt.launch_listener() #start listener, then flip local & cloud 'connected' == "1"
        cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"connected","1", db_writer = dbt.patch_firebase)
    
        #update the device state to "connected"
        print("Device is connected over HTTPS to the Oasis Network")
        
    except Exception as e:
        #print(err.full_stack()) #display error
        #write state as not connected
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0", db_writer = dbt.patch_firebase)
        print("Could not establish an HTTPS connection to Oasis Network")

if __name__ == "__main__":
    connect_to_firebase()