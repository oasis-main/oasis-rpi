#File for all database functions
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/core')
sys.path.append('/home/pi/oasis-grow/utils')

import requests
import json
import pyrebase
import multiprocessing
from subprocess import Popen

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
    def send_data(field, value):
        data = json.dumps({field: value})
        url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
        result = requests.patch(url,data)
        return result
    
    patch_request = multiprocessing.Process(target = send_data, args = [field, value])
    patch_request.start()

#modifies a firebase variable, now asynchroous
def patch_firebase_dict(access_config, data): #Depends on: load_state(),'requests','json'; Modifies: database['field'], state variables
    def send_data(data):
        data = json.dumps(data)
        url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
        result = requests.patch(url,data)
        return result
    
    patch_request = multiprocessing.Process(target = send_data, args = [data])
    patch_request.start()

#stores a file in firebase storage
def store_file(user, storage, path, device_name, filename):
    storage.child(user['userId'] + "/" + device_name + "/" + filename).put(path, user['idToken'])

#gets new refresh token from firebase
def get_refresh_token(web_api_key,email,password): #Depends on: 'requests', 'json', cs.write_state; Modifies: None
    sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + web_api_key
    sign_in_payload = json.dumps({"email": email, "password": password, "returnSecureToken": "true"})
    r = requests.post(sign_in_url, sign_in_payload)
    data = json.loads(r.content)
    return data["refreshToken"]

#get local_id and id_token from firebase
def get_local_credentials(wak,refresh_token): #Depends on: cs.load_state(), cs.write_state(), 'requests'; Modifies: state variables,  cs.access_config.json
    #get local credentials
    refresh_url = "https://securetoken.googleapis.com/v1/token?key=" + wak
    refresh_payload = '{"grant_type": "refresh_token", "refresh_token": "%s"}' % refresh_token
    refresh_req = requests.post(refresh_url, data=refresh_payload)
    id_token = refresh_req.json()["id_token"]
    user_id = refresh_req.json()["user_id"]
    return id_token, user_id

#launches a script to detect changes in the database
def launch_listener(): #depends on 'subprocess', modifies: state variables
    global listener
    listener = Popen(["python3", "/home/pi/oasis-grow/networking/detect_db_events.py"])

def kill_listener():
    global listener
    listener = None

def fetch_device_data(access_config):
    url = "https://oasis-state-af548-default-rtdb.firebaseio.com/"+str(access_config["local_id"])+"/"+str(access_config["device_name"])+".json?auth="+str(access_config["id_token"])
    result = requests.get(url)
    decoded_result = result.content.decode()
    cloud_data = json.loads(decoded_result)
    return cloud_data

