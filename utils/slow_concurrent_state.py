#import modules
import os
import sys
import time

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#rust modules
import json #fast data interchange / and json parsing (must read and write byte file objects)

#oasis utilities
from utils import reset_model
from utils import error_handler as err

#___________________________________________________________________
#Declare Structs

#...cloud-synced:
#device_state #describes the current state of the system
#control_params #describes the grow configuration of the system

#...cloud-touching
#sensor_data #tells the system which features are in use (data only goes out)
#feature_toggles #tells the system which features are in use (data comes in, but in a manually activated flow)

#...locally-kept
#access_config #contains credentials for connecting to firebase
#hardware_config #holds hardware I/O setting & pin

structs = {"device_state": {}, 
"control_params": {}, 
"sensor_data": {}, 
"access_config" : {}, 
"hardware_config": {}, 
"feature_toggles": {}}

#declare state locking varibles
locks = {}
lock_filepath = "/home/pi/oasis-grow/configs/locks.json"

def load_state(loop_limit=1000): 
    global structs

    for struct in structs: #now we're going to load an populate the data    

        #load device state
        for i in list(range(int(loop_limit))): #try to load, pass and try again if fails
            try:
                config_filepath = "/home/pi/oasis-grow/configs/" + struct + ".json"

                if not os.path.exists(config_filepath):
                    print(config_filepath + " does not exist. Have you run the setup scripts?")
                    return

                with open(config_filepath, "r") as x: #open the config filepath with bytes
                        structs[struct] = json.load(x) #try to parse bytes to json -> dict
                        #print(struct)

                for k in structs[struct]: 
                    #print(k)
                    if structs[struct][k] is None:
                        print("Read NoneType in " + struct + "!")
                        print("Resetting " + struct + "...") 
                        reset_model.reset_config_path(config_filepath)
                    
                    else: 
                        pass
            
                break
                
            except Exception as e:
                if i >= int(loop_limit):
                    reset_model.reset_config_path(config_filepath)
                    print("Tried to read " + struct + " max # of times. File is corrupted, resetting...")
                else:
                    #print(err.full_stack())
                    #print("Tried to read " + struct + "while being written. If this continues, file is corrupt.")
                    pass

#gets the mutex
def load_locks(loop_limit = 10000): #leave this alone since it's the python bridge to ramport locks
    global locks
    
    lock_filepath = "/home/pi/oasis-grow/configs/locks.json"
            
    if not os.path.exists(lock_filepath):
        print("Lockfile does not exist. Have you run the setup scripts?")
        return
    
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open(lock_filepath, "r") as l:
                locks = json.load(l) #get locks
                #print(type(locks))

            for k,v in locks.items():
                if locks[k] is None:
                    print("Read NoneType in locks")
                    print("Resetting lock...")
                    unlock(lock_filepath,k)  
                else: 
                    pass
             
            break   
    
        except Exception as e:
            if i >= (loop_limit-1):
                print("Tried to load locks max number of times. File is corrupted. Resetting locks...")
                print(err.full_stack())
                reset_locks(lock_filepath)
            else:
                print("Main.py tried to read while locks were being written. If this continues, file is corrupted.")
                print(err.full_stack())
                pass

    return lock_filepath

def lock(lock_filepath: str, resource_key: str):
    global locks

    with open(lock_filepath, "w") as x:
        locks[resource_key] = 1 #write the desired value
        x.seek(0)
        json.dump(locks,x)
        x.truncate()

def unlock(lock_filepath: str, resource_key: str):
    global locks

    with open(lock_filepath, "w") as x:
        locks[resource_key] = 0 #write the desired value
        x.seek(0)
        json.dump(locks,x)
        x.truncate()

def reset_locks(lock_filepath):
    global locks

    for lock in locks:
        locks[lock] = 0
    
    with open(lock_filepath, "w") as x:
        x.seek(0)
        json.dump(locks,x)
        x.truncate()

#save key values to .json
def write_state(path, field, value, db_writer = None, loop_limit=2500): #Depends on: load_state()
    if db_writer is not None: #Accepts(path, field, value, custom timeout, db_writer function); Modifies: path
        if structs["device_state"]["connected"] == "1": #write state to cloud
            try:
                db_writer(structs["access_config"],field,value) #will be loaded in by listener, so is best represent change db first
            except Exception:
                print(err.full_stack())
                pass
            
    if not os.path.exists(path):
        print(path + " does not exist. Have you run the setup scripts?")
        return

    lock_filepath = load_locks() #get all the mutexes

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke if so 
        try:
            with open(path, "r") as x: # open the file.
                data = json.load(x) # can we load a valid json?

            if locks[path] == 0: #check is the file is available to be written
                
                lock(lock_filepath, path)

                with open(path, "w") as x:
                    data[field] = value #write the desired value
                    x.seek(0)
                    json.dump(data,x)
                    x.truncate()

                unlock(lock_filepath, path)
                
                load_state()
                break #break the loop when the write has been successful

            else:
                if i >= int(loop_limit):
                    print("Tried to access "+ path + " max # of times. Lock is dead. Resetting...")
                    unlock(lock_filepath, path)
                    
                    #Now write safely
                    lock(lock_filepath, path)

                    with open(path, "w") as x:
                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data,x)
                        x.truncate()

                    unlock(lock_filepath, path)
                    
                    load_state()
                    
                    break #break the loop when the write has been successful
                else:
                    print("Waiting...")
                    pass

        except Exception as e: #If any of the above fails
            if i >= int(loop_limit):
                print(err.full_stack())
                print("Tried to write "+ path + " max # of times. File is corrupted. Resetting...")
                reset_model.reset_config_path(path)
                
                #now write
                with open(path, "r") as x: # open the file.
                    data = json.load(x) # can we load a valid json?
                    
                #only call this once with path or other unique string as argument
                
                if locks[path] == 0: #check is the file is available to be written
                    lock(lock_filepath, path)
                    
                    with open(path, "w") as x:
                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data,x)
                        x.truncate()

                    unlock(lock_filepath, path)
                    
                    load_state()    

                break
            else:
                print(path + " write failed, trying again. If this persists, file is corrupted.")
                print(err.full_stack())
                pass #continue the loop until write is successful or ceiling is hit

#save key values to .json
def write_dict(path, dictionary, db_writer = None, loop_limit=2500): #Depends on: load_state(), dbt.patch_firebase, 'json'; Modifies: path

    if db_writer is not None:
        #these will be loaded in by the listener, so best to make sure we represent the change in firebase too
        if structs["device_state"]["connected"] == "1": #write state to cloud
            try:
                db_writer(structs["access_config"], dictionary)
            except Exception:
                print(err.full_stack())
                pass

    lock_filepath = load_locks()

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke if so
        try:
            with open(path, "r") as x: # open the file.
                data = json.load(x) # can we load a valid json?
                
            #only call this once with path or other unique string as argument
            
            if locks[path] == 0: #check is the file is available to be written
                lock(lock_filepath, path)

                with open(path, "w") as x:
                    data.update(dictionary) #write the desired values
                    x.seek(0)
                    x.write(json.dump(data,x))
                    x.truncate()

                unlock(lock_filepath, path)
                
                load_state()
                break #break the loop when the write has been successful

            else:
                if i >= int(loop_limit):
                    print("Tried to access "+ path + " max # of times. Lock is dead. Resetting...")
                    unlock(lock_filepath, path)
                    
                    #Now write safely
                    lock(lock_filepath, path)

                    with open(path, "w") as x:
                        data.update(dictionary) #write the desired values
                        x.seek(0)
                        json.dump(data,x)
                        x.truncate()

                    unlock(lock_filepath, path)
                    
                    load_state()
                    
                    break #break the loop when the write has been successful
                else:
                    print("Waiting...")
                    pass

        except Exception: #If any of the above fails:
            if i >= int(loop_limit):
                print("Tried to write "+ path + " max # of times. File is corrupted. Resetting...")
                reset_model.reset_config_path(path)
                
                #now write
                with open(path, "r") as x: # open the file.
                    data = json.load(x) # can we load a valid json?
                    
                    #only call this once with path or other unique string as argument
                    
                    if locks[path] == 0: #check is the file is available to be written
                        lock(lock_filepath, path)

                        with open(path, "w") as x:
                            data.update(dictionary) #write the desired values
                            x.seek(0)
                            json.dump(data,x)
                            x.truncate()

                        unlock(lock_filepath, path)
                        
                        load_state()
                
                break

            else:
                print(path + " write failed, trying again. If this persists, file is corrupted.")
                print(err.full_stack())
                pass #continue the loop until write is successful or ceiling is hit

def check_lock(resource):
    load_locks()
    if locks[resource] == 1: #if resource is locked
        print(resource + " is currently in use by another process.")
        sys.exit() #termiating for safety
    else:
        lock(lock_filepath, resource)

if __name__ == '__main__':
    print("This is a unit test:")
    load_state()
    load_locks()
    write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "1")
    write_dict("/home/pi/oasis-grow/configs/device_state.json", {"running": "1"})
