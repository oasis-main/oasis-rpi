#https://stackoverflow.com/questions/58354509/modulenotfounderror-no-module-named-python-jwt-raspberry-pi
#https://github.com/thisbejim/Pyrebase
#https://stackoverflow.com/questions/45154853/how-to-detect-changes-in-firebase-child-with-python


#this may be helpful if i cant figure something else out for updating values
#https://pypi.org/project/FirebaseData/

#This may be the thing to do
#https://github.com/thisbejim/Pyrebase/issues/341

#OTHER
#________________
#https://stackoverflow.com/questions/62301320/pyrebase-and-firebase-database-rules-how-to-deal-with-it-with-python
#https://www.reddit.com/r/Firebase/comments/idhdji/how_can_i_store_data_under_a_user_id_with_pyrebase/g2bcvhz/
#https://medium.com/@parasmani300/pyrebase-firebase-in-flask-d249a065e0df
#https://stackoverflow.com/questions/54838847/pyrebase-stream-retrived-data-access

import os
import os.path
import sys
import time

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

import signal
import pyrebase
from multiprocessing import Process, Queue
import json
from utils import concurrent_state as cs
from utils import error_handler as err
from networking import db_tools as dbt

#declare listener list
listener_list = []

def stream_handler(m):
    #ok some kind of update
    #might be from start up or might be user changed it
    if m['event']=='put':
        #act_on_event(m['stream_id'],m['data'])
        print(m)

    #something else
    else:
        pass
        #if this happens... theres a problem...
        #should be handled for
        print('something wierd...', m['event'])
        input()

@err.Error_Handler
def detect_field_event(user, db):
    my_stream = db.child(user['userId']+'/'+cs.access_config["device_name"]+"/").stream(stream_handler, user['idToken'])

#https://stackoverflow.com/questions/2046603/is-it-possible-to-run-function-in-a-subprocess-without-threading-or-writing-a-se
#https://stackoverflow.com/questions/200469/what-is-the-difference-between-a-process-and-a-thread#:~:text=A%20process%20is%20an%20execution,sometimes%20called%20a%20lightweight%20process.
#run multiprocesser to handle database listener
#could use threads in future? would it be better?
def detect_multiple_field_events(user, db, fields):
    global listner_list

    p = Process(target=detect_field_event, args=(user, db))
    p.start()
    listener_list.append(p)

    '''
    for field in fields:
        p = Process(target=detect_field_event, args=(user, db))
        p.start()
        listener_list.append(p)
    '''

#This function launches a thread that checks whether the device has been deleted and kills this script if so
def stop_condition(field,value): #Depends on: os, Process,cs.load_state(); Modifies: listener_list, stops this whole script
    global listener_list

    def check_exit(f,v): #This should be launched in its own thread, otherwise will hang the script
        while True:
            try:
                cs.load_state()
            except:
                pass

            if cs.device_state[f] == v:
                print("Exiting database listener...")
                for listener in listener_list:
                    listener.terminate()
                os._exit(0)

    stop_condition = Process(target = check_exit, args = (field,value))
    stop_condition.start()

#make change to config file
def act_on_event(field, new_data):
    #get data and field info

    #checks if file exists and makes a blank one if not
    #the path has to be set for box
    device_state_fields = list(cs.device_state.keys())
    device_params_fields = list(cs.device_params.keys())

    if str(field) in device_state_fields:
        path = "/home/pi/oasis-grow/configs/device_state.json"
    if str(field) in device_params_fields:
        path = "/home/pi/oasis-grow/configs/device_params.json"

    if os.path.exists(path) == False:
        f = open(path, "w")
        f.write("{}")
        f.close()

    #open data config file
    #edit appropriate spot
    #print(path)
    cs.write_state(path, field, new_data, offline_only = True)

if __name__ == "__main__":
    print("Starting listener...")
    cs.load_state()
    try:
        user, db = dbt.initialize_user(cs.access_config["refresh_token"])
        print("Database monitoring: active")
    except Exception as e:
        print("Listener could not connect")
        print("Database monitoring: inactive")
        sys.exit()
    
    print(dbt.get_user_data(user, db))
    
    #actual section that launches the listener
    device_state_fields = list(cs.device_state.keys())
    device_params_fields = list(cs.device_params.keys())
    fields = device_state_fields + device_params_fields
    
    detect_multiple_field_events(user, db, fields)
    stop_condition("deleted","1")
    stop_condition("connected", "0")

