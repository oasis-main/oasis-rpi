#This file contains tools for managing shared state in a python multiprocessing application
#Used in:
##main.py
##core.py
##update.py
##camera.py
##connect_oasis(offline only)
##detect_db_events(offline only)

#import modules
import os
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

#rust modules
import orjson #fast data interchange / and json parsing (must read and write byte file objects)
import rusty_locks as safety #rust concurrency modules (fast mutual exclusion for arbitrarily named resources) 

#oasis utilities
from utils import reset_model
from utils import error_handler as err

#___________________________________________________________________
#Declare Structs

#...cloud-synced:
#device_state #describes the current state of the system
#device_params #describes the grow configuration of the system

#...cloud-touching
#sensor_info #tells the system which features are in use (data only goes out)
#feature_toggles #tells the system which features are in use (data comes in, but in a manually activated flow)

#...locally-kept
#access_config #contains credentials for connecting to firebase
#hardware_config #holds hardware I/O setting & pin

structs = {"device_state": {}, 
"device_params": {}, 
"sensor_info": {}, 
"access_config" : {}, 
"hardware_config": {}, 
"feature_toggles": {}}

#declare state locking varibles
locks = None

def load_state(loop_limit=1000): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global structs

    for struct in structs: #now we're going to load an populat the data    

        #load device state
        for i in list(range(int(loop_limit))): #try to load, pass and try again if fails
            try:
                if struct != 'sensor_info':
                    config_filepath = "/home/pi/oasis-grow/configs/" + struct + ".json"
                else:
                    config_filepath = "/home/pi/oasis-grow/data_out/" + struct + ".json"

                if not os.path.exists(config_filepath):
                    print(config_filepath + " does not exist. Have you run the setup scripts?")
                    return

                with open(config_filepath, "rb") as x: #open the config filepath with bytes
                        structs[struct] = orjson.loads(x.read()) #try to parse bytes to json -> dict
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
            with open(lock_filepath, "rb") as l:
                locks = orjson.loads(l.read()) #get locks

            for k,v in locks.items():
                if locks[k] is None:
                    print("Read NoneType in locks")
                    print("Resetting lock...")
                    safety.unlock(lock_filepath,k)  
                else: 
                    pass
             
            break   
    
        except Exception as e:
            if i == int(loop_limit):
                print("Tried to load locks max number of times. File is corrupted. Resetting locks...")
                safety.reset_locks(lock_filepath)
            else:
                print("Main.py tried to read while locks were being written. If this continues, file is corrupted.")
                pass

    return lock_filepath

#save key values to .json
def write_state(path, field, value, db_writer = None, loop_limit=1000): #Depends on: load_state(), 'json'; 
    if db_writer is not None: #Accepts(path, field, value, custom timeout, db_writer function); Modifies: path
        if structs["device_state"]["connected"] == "1": #write state to cloud
            try:
                db_writer(structs["access_config"],field,value) #will be loaded in by listener, so is best represent change db first
            except Exception as e:
                print(err.full_stack())
                pass
            
    if not os.path.exists(path):
        print(path + " does not exist. Have you run the setup scripts?")
        return

    lock_filepath = load_locks() #get all the mutexes

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke if so 
        try:
            with open(path, "wb") as x: # open the file.
                data = orjson.loads(x.read()) # can we load a valid json?

                if locks[path] == 0: #check is the file is available to be written
                    
                    safety.lock(lock_filepath, path)

                    data[field] = value #write the desired value
                    x.seek(0)
                    x.write(orjson.dumps(data))
                    x.truncate()

                    safety.unlock(lock_filepath, path)
                    
                    load_state()
                    break #break the loop when the write has been successful

                else:
                    if i >= int(loop_limit):
                        print("Tried to access "+ path + " max # of times. Lock is dead. Resetting...")
                        safety.unlock(lock_filepath, path)
                        
                        #Now write safely
                        safety.lock(lock_filepath, path)

                        data[field] = value #write the desired value
                        x.seek(0)
                        x.write(orjson.dumps(data))
                        x.truncate()

                        safety.unlock(lock_filepath, path)
                        
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
                with open(path, "wb") as x: # open the file.
                    data = orjson.loads(x.read()) # can we load a valid json?
                    
                    #only call this once with path or other unique string as argument
                    
                    if locks[path] == 0: #check is the file is available to be written
                        safety.lock(lock_filepath, path)
                        
                        data[field] = value #write the desired value
                        x.seek(0)
                        x.write(orjson.dumps(data))
                        x.truncate()

                        safety.unlock(lock_filepath, path)
                        
                        load_state()    

                break
            else:
                print(path + " write failed, trying again. If this persists, file is corrupted.")
                print(err.full_stack())
                pass #continue the loop until write is successful or ceiling is hit

#save key values to .json
def write_dict(path, dictionary, db_writer = None, loop_limit=1000): #Depends on: load_state(), dbt.patch_firebase, 'json'; Modifies: path

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
            with open(path, "wb") as x: # open the file.
                data = orjson.loads(x.read()) # can we load a valid json?
                
                #only call this once with path or other unique string as argument
                
                if locks[path] == 0: #check is the file is available to be written
                    safety.lock(lock_filepath, path)

                    data.update(dictionary) #write the desired values
                    x.seek(0)
                    x.write(orjson.dumps(data))
                    x.truncate()

                    safety.unlock(lock_filepath, path)
                    
                    load_state()
                    break #break the loop when the write has been successful

                else:
                    if i >= int(loop_limit):
                        print("Tried to access "+ path + " max # of times. Lock is dead. Resetting...")
                        safety.unlock(lock_filepath, path)
                        
                        #Now write safely
                        safety.lock(lock_filepath, path)

                        data.update(dictionary) #write the desired values
                        x.seek(0)
                        x.write(orjson.dumps(data))
                        x.truncate()

                        safety.unlock(lock_filepath, path)
                        
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
                with open(path, "wb") as x: # open the file.
                    data = orjson.loads(x.read()) # can we load a valid json?
                    
                    #only call this once with path or other unique string as argument
                    
                    if locks[path] == 0: #check is the file is available to be written
                        safety.lock(lock_filepath, path)

                        data.update(dictionary) #write the desired values
                        x.seek(0)
                        x.write(orjson.dumps(data))
                        x.truncate()

                        safety.unlock(lock_filepath, path)
                        
                        load_state()
                
                break

            else:
                print(path + " write failed, trying again. If this persists, file is corrupted.")
                print(err.full_stack())
                pass #continue the loop until write is successful or ceiling is hit

#Higher-order device_state checker
def check(state, function, args = None, kwargs = None, alt_function = None, alt_args = None, alt_kwargs = None):
    load_state()
    if structs["device_state"][state] == "1":
        if (args is None) & (kwargs is None):
            function()
        if (args is not None) & (kwargs is None):
            function(*args)
        if (args is None) & (kwargs is not None):
            function(**kwargs)
        if (args is not None) & (kwargs is not None):
            function(*args,**kwargs)
    else:
        if (alt_args is None) & (alt_kwargs is None):
            alt_function()
        if (alt_args is not None) & (alt_kwargs is None):
            alt_function(*alt_args)
        if (alt_args is None) & (alt_kwargs is not None):
            alt_function(**alt_kwargs)
        if (alt_args is not None) & (alt_kwargs is not None):
            alt_function(*alt_args,**alt_kwargs)
        else:
            pass

if __name__ == "__main__":
    print("This is a unit test:")
    load_state()
    load_locks()
    write_state("/home/pi/oasis-grow/configs/device_state.json", "running", "1")
    write_dict("/home/pi/oasis-grow/configs/device_state.json", {"running": "1"})
