#File for all database functions
import os
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import requests
import json
import pyrebase
import multiprocessing

from utils import concurrent_state as cs
from utils import error_handler as err

listener = None

def initialize_user(RefreshToken):

    #app configuration information
    config = {
    "apiKey": "AIzaSyBPuJwU--0ZlvsbDV9LmKJdYIljwNwzmVk",
    "authDomain": "oasis-state-af548.firebaseapp.com",
    "databaseURL": "https://oasis-state-af548-default-rtdb.firebaseio.com/",
    "storageBucket": "oasis-state-af548.appspot.com"
    }

    firebase = pyrebase.initialize_app(config)

    # Get a reference to the auth service
    auth = firebase.auth()
    # Get a reference to the database service
    db = firebase.database()
    # Get a reference to the storage service
    storage = firebase.storage()

    #input by user on setup
    user = auth.refresh(RefreshToken)

    return user, db, storage

#get all user data
def get_user_data(user, db):
    return  db.child(user['userId']).get(user['idToken']).val()

#modifies a firebase variable, now asynchroous
def patch_firebase(access_config,field,value): #Depends on: load_state(),'requests','json'; Modifies: database['field'], state variables
    data = json.dumps({field: value})
    url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)
    return result

def firebase_add_device(access_config,data): #Depends on: load_state(),'requests','json'; Modifies: database['field'], state variables
    data = json.dumps(data)
    url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+str(access_config["local_id"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)
    return result

#modifies a firebase variable, now asynchroous
def patch_firebase_dict(access_config, data): #Depends on: load_state(),'requests','json'; Modifies: database['field'], state variables
    data = json.dumps(data)
    url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.patch(url,data)
    return result

#stores a file in firebase storage
def store_file(user, storage, path, device_name, filename):
    storage.child(user['userId'] + "/" + device_name + "/" + filename).put(path, user['idToken'])

#gets new refresh token from firebase
def get_refresh_token(web_api_key,email,password): #Depends on: 'requests', 'json'; Modifies: None
    sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + web_api_key
    sign_in_payload = json.dumps({"email": email, "password": password, "returnSecureToken": "true"})
    r = requests.post(sign_in_url, sign_in_payload)
    data = json.loads(r.content)
    return data["refreshToken"]

#get local_id and id_token from firebase
def get_local_credentials(wak,refresh_token): #Depends on: cs.load_state(), 'requests'; Modifies: state variables,  cs.access_config.json
    #get local credentials
    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
    refresh_req = requests.post(refresh_url, data=refresh_payload)
    id_token = refresh_req.json()["id_token"]
    user_id = refresh_req.json()["user_id"]
    return id_token, user_id

def fetch_device_data(access_config):
    url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.get(url)
    decoded_result = result.content.decode()
    cloud_data = json.loads(decoded_result)
    return cloud_data

#sync local configuration with 
def sync_state():
    cloud_data = fetch_device_data()
    for key_value_pair in list(cloud_data.items()):
        if key_value_pair[0] in list(cs.device_state.keys()):
            #print("Updating device_state")
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json", key_value_pair[0], key_value_pair[1], db_writer = None)
        elif key_value_pair[0] in list(cs.device_params.keys()):
            #print("Updating device_params")
            cs.write_state("/home/pi/oasis-grow/configs/device_params.json", key_value_pair[0], key_value_pair[1], db_writer = None)    
        else:
            #print("Not working")
            pass

#make change to config file
def act_on_event(field, new_data):
    #get data and field info

    #checks if file exists and makes a blank one if not
    #the path has to be set for box
    device_state_fields = list(cs.device_state.keys())
    device_params_fields = list(cs.device_params.keys())

    path = " "

    if field in device_state_fields:
        path = "/home/pi/oasis-grow/configs/device_state.json"
    elif field in device_params_fields:
        path = "/home/pi/oasis-grow/configs/device_params.json"

    if os.path.exists(path) == False:
        return

    #open data config file
    #edit appropriate spot
    #print(path)
    cs.write_state(path, field, new_data, db_writer = None)

def stream_handler(m):
    #some kind of update
    #might be from start up or might be user changed it
    if m['event']=='put' or m['event']=='patch':
        print(m)
        print(m['path'])
        
        field = str(m['path']).replace("/","")
        print(field)
        
        act_on_event(field, m['data'])

    #something else
    else:
        #if this happens... theres a problem...
        #should be handled for
        print('something wierd...', m['event'])
        pass

@err.Error_Handler
def detect_field_event(user, db):
    my_stream = db.child(user['userId']+'/'+cs.access_config["device_name"]+"/").stream(stream_handler, user['idToken'])

#https://stackoverflow.com/questions/2046603/is-it-possible-to-run-function-in-a-subprocess-without-threading-or-writing-a-se
#https://stackoverflow.com/questions/200469/what-is-the-difference-between-a-process-and-a-thread#:~:text=A%20process%20is%20an%20execution,sometimes%20called%20a%20lightweight%20process.
#run multiprocesser to handle database listener
def detect_multiple_field_events(user, db):
    global listener

    listener = multiprocessing.Process(target=detect_field_event, args=(user, db))
    listener.start()

#This function launches a thread that checks whether the device has been deleted and kills this script if so
def stop_condition(field,value): #Depends on: os, Process,cs.load_state(); Modifies: listener_list, stops this whole script

    def check_exit(f,v): #This should be launched in its own thread, otherwise will hang the script
        while True:
            try:
                cs.load_state()
            except:
                pass

            if cs.device_state[f] == v:
                print("Exiting database listener...")
                kill_listener()

    stop_condition = multiprocessing.Process(target = check_exit, args = (field,value))
    stop_condition.start()

def run():
    print("Starting listener...")
    cs.load_state()
    try:
        user, db, storage = initialize_user(cs.access_config["refresh_token"])
        
        #fetch all the most recent data from the database
        fetch_device_data(cs.access_config)
        
        #actual section that launches the listener
        detect_multiple_field_events(user, db)
        stop_condition("awaiting_deletion","1")
        stop_condition("connected", "0")
        
        print("Database monitoring: active")
    except Exception:
        print(err.full_stack())
        print("Listener could not connect")
        print("Database monitoring: inactive")

#launches a script to detect changes in the database
def launch_listener(): #depends on 'subprocess', modifies: state variables
    global listener
    listener =  multiprocessing.Process(target = run)
    listener.start()

def kill_listener():
    global listener
    listener.terminate()
    listener = None
