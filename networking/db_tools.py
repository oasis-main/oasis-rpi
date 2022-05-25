#File for all database functions
#Import and call from another location

from asyncio import subprocess
import os
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')

import requests
import json
import time
import pyrebase
import multiprocessing
from subprocess import Popen

from utils import concurrent_state as cs
from utils import reset_model

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

    #WILL NEED TO GET THIS FROM USER
    user = auth.refresh(RefreshToken)

    return user, db

#get all user data
def get_user_data(user, db):
    return  db.child(user['userId']).get(user['idToken']).val()

def send_image(user, storage, path):
    #send new image to firebase
    storage.child(user['userId'] + "/" + cs.access_config["device_name"] + "/image.jpg").put(path, user['idToken'])
    print("sent image")

    #tell firebase that there is a new image
    cs.patch_firebase("new_image","1")
    print("firebase has an image in waiting")

#gets new refresh token from firebase
def get_refresh_token(web_api_key,email,password): #Depends on: 'requests', 'json', cs.write_state; Modifies: None
    sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + web_api_key
    sign_in_payload = json.dumps({"email": email, "password": password, "returnSecureToken": "true"})
    r = requests.post(sign_in_url, sign_in_payload)
    data = json.loads(r.content)
    return data["refreshToken"]

#get local_id and id_token from firebase
def get_local_credentials(refresh_token): #Depends on: cs.load_state(), cs.write_state(), 'requests'; Modifies: state variables,  cs.access_config.json
    #load state so we can use access credentials
    cs.load_state()
    wak = cs.access_config["wak"]

    #get local credentials
    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
    refresh_req = requests.post(refresh_url, data=refresh_payload)

    #write local credentials to access config
    cs.write_state("/home/pi/oasis-grow/configs/access_config.json","id_token",refresh_req.json()["id_token"])
    cs.write_state("/home/pi/oasis-grow/configs/access_config.json","local_id",refresh_req.json()["user_id"])

    print("Obtained local credentials")

#connects system to firebase
def connect_firebase(): #depends on: cs.load_state(), cs.write_state(), cs.patch_firebase(), 'requests'; Modifies: access_config.json, device_state.json
    
    def try_connect():
   
        #load state so we can use access credentials
        cs.load_state()
        wak = cs.access_config["wak"]
        email = cs.access_config["e"]
        password = cs.access_config["p"]

        print("Checking for connection...")

        try:
            print("FireBase verification...")

            #fetch refresh token
            refresh_token = get_refresh_token(wak, email, password)

            #fetch refresh token and save to access_config
            cs.write_state("/home/pi/oasis-grow/configs/access_config.json","refresh_token", refresh_token)

            #bring in the refresh token for use further down
            cs.load_state()
            refresh_token = cs.access_config["refresh_token"]
            print("Obtained refresh token")

            #fetch a new id_token & local_id
            get_local_credentials(refresh_token)

            #launch checks at network startup
            check_new_device()
            check_updates()
            check_deleted()

            #start listener to bring in db changes, make a status flag for the mqqt process
            #TODO

            #update the device state to "connected"
            cs.write_state('/home/pi/oasis-grow/configs/device_state.json',"connected","1")
            print("Device is connected over HTTPS to the Oasis Network")

            cs.load_state()
            
        except Exception as e:
            print(e) #display error
            #write state as not connected
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0")
            print("Could not establish an HTTPS connection to Oasis Network")

    time.sleep(15)
    connection_attempt = multiprocessing.Process(target = try_connect)
    connection_attempt.start()

#check if the device is waiting to be added to firebase, if it is then add it, otherwise skip
def check_new_device(): #depends on: modifies:
    cs.load_state()

    if cs.device_state["new_device"] == "1":

        #assemble data to initialize firebase
        setup_dict = {} #Access & hardware config will be kept private, not shared with cloud 
        setup_dict.update(cs.device_state)
        setup_dict.update(cs.device_params)
        setup_dict.update(cs.feature_toggles)
        setup_dict.update(cs.sensor_info)
        setup_dict_named = {cs.access_config["device_name"] : setup_dict}
        my_data = json.dumps(setup_dict_named)
        #print(my_data)
        #print(type(my_data))

        #add box data to firebase
        url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+cs.access_config["local_id"]+".json?auth="+cs.access_config["id_token"]
        post_request = requests.patch(url,my_data)
        #print(post_request.ok)
        if post_request.ok:
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json","new_device","0")
            print("New device added to firebase")
        else:
            print("Failed to add new device")

#checks for available updates, executes if connected & idle, waits for completion
def check_updates(): #depends on: cs.load_state(),'subproceess', update.py; modifies: system code, state variables
    cs.load_state()
    if cs.device_state["running"] == "0" and cs.device_state["awaiting_update"] == "1": #replicated in the main loop
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
    if cs.device_state["running"] == "1" and cs.device_state["awaiting_update"] == "1": #replicated in the main loop
        #flip running to 0        
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","0")
        #kill listener
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        #launch update.py and wait to complete
        update_process = Popen(["python3", "/home/pi/oasis-grow/utils/update.py"])
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","running","1") #restore running
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","1")#restore listener
        output, error = update_process.communicate()
        if update_process.returncode != 0:
            print("Failure " + str(update_process.returncode)+ " " +str(output)+str(error))
            
#launches a script to detect changes in the database
def launch_listener(): #depends on 'subprocess', modifies: state variables
    global listener
    listener = Popen(["python3", "/home/pi/oasis-grow/networking/db_listener.py"])

#deletes a box if the cloud is indicating that it should do so
def check_deleted():
    global listener
    cs.load_state()
    if cs.device_state["deleted"] == "1" and listener is not None:
        print("Removing device from Oasis Network...")
        cs.write_state("/home/pi/oasis-grow/configs/device_state.json","connected","0") #make sure it doesn't write anything to the cloud, kill the listener
        listener = None
        print("Database monitoring deactivated")
        reset_model.reset_nonhw_configs()
        print("Device has been reset to default configuration")
        systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])

if __name__ == "main":
    cs.load_state()
    user, db = initialize_user(cs.access_config["refresh_token"])
    get_user_data(user, db)
