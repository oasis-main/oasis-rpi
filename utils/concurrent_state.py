#This file contains tools for managing shared state in a python multiprocessing application
#Used in:
##main.py
##core.py
##update.py
##camera.py
##connect_oasis(offline only)
##detect_db_events(offline only)

#import modules
import sys
import json

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

from utils import reset_model

#declare state variables
device_state = None #describes the current state of the system
device_params = None #describes the grow configuration of the system
sensor_info = None
hardware_config = None #holds hardware I/O setting & pin #s
access_config = None #contains credentials for connecting to firebase
feature_toggles = None #tells the system which features are in use

#declare state locking varibles
locks = None

def load_state(loop_limit=100000): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, device_params, sensor_info, access_config, feature_toggles, hardware_config

    #load device state
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke if so,  
        try:
            with open("/home/pi/oasis-grow/configs/device_state.json") as d:
                device_state = json.load(d) #get device state

            for k,v in device_state.items(): 
                if device_state[k] is None:
                    print("Read NoneType in device_state")
                    print("Resetting device_state...") 
                    reset_model.reset_device_state()
                else: 
                    pass
        
            break
            
        except Exception as e:
            if i >= int(loop_limit):
                reset_model.reset_device_state()
                print("Main.py tried to read max # of times. File is corrupted. Resetting device state ...")
            else:
                print("Main.py tried to read while file was being written. If this continues, file is corrupted.")
                pass
    
    #load device_params
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/configs/device_params.json") as p:
                device_params = json.load(p) #get device params

            for k,v in device_params.items(): 
                if device_params[k] is None:
                    print("Read NoneType in device_params")
                    print("Resetting device_params...")
                    reset_model.reset_device_params()
                     
                else: 
                    pass    
        
            break
            
        except Exception as e:
            if i == int(loop_limit):
                print("Main.py tried to read max # of times. File is corrupted. Resetting device_params...")
                reset_model.reset_device_params()
            else:
                print("Main.py tried to read while device_params was being written. If this continues, file is corrupted.")
                pass   

    #load sensor_info
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/data_out/sensor_info.json") as s:
                sensor_info = json.load(s) #get sensor info

            for k,v in sensor_info.items(): 
                if sensor_info[k] is None:
                    print("Read NoneType key in sensor_info")
                    print("Resetting sensor_info...")
                    #reset_model.reset_sensor_info()
                     
                else: 
                    pass    
        
            break
            
        except Exception as e:
            if i == int(loop_limit):
                print("Main.py tried to read max # of times. File is corrupted. Resetting device_params...")
                reset_model.reset_device_params()
            else:
                print("Main.py tried to read while sensor_info was being written. If this continues, file is corrupted.")
                pass   

    #load access_config
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/configs/access_config.json") as a:
                access_config = json.load(a) #get access_config

            for k,v in access_config.items(): 
                if access_config[k] is None:
                    print("Read NoneType in access_config")
                    print("Resetting access_config...")
                    reset_model.reset_access_config()
                     
                else: 
                    pass    
        
            break
            
        except Exception as e:
            if i == int(loop_limit):
                print("Main.py tried to read max # of times. File is corrupted. Resetting access_config...")
                reset_model.reset_access_config()
            else:
                print("Main.py tried to read while access_config was being written. If this continues, file is corrupted.")
                pass               

    #load feature_toggles
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/configs/feature_toggles.json") as f:
                feature_toggles = json.load(f) #get feature_toggles

            for k,v in feature_toggles.items(): 
                if feature_toggles[k] is None:
                    print("Read NoneType in feature_toggles")
                    print("Resetting feature_toggles...")
                    reset_model.reset_feature_toggles()
                     
                else: 
                    pass    
        
            break
            
        except Exception as e:
            if i == int(loop_limit):
                print("Main.py tried to read max # of times. File is corrupted. Resetting feature_toggles...")
                reset_model.reset_feature_toggles()
            else:
                print("Main.py tried to read while feature_toggles was being written. If this continues, file is corrupted.")
                pass
            
    #load hardware_config
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/configs/hardware_config.json") as h:
                hardware_config = json.load(h) #get hardware config

            for k,v in hardware_config.items(): 
                if hardware_config[k] is None:
                    print("Read NoneType in hardware_config")
                    print("Resetting hardware_config...")
                    reset_model.reset_hardware_config()
                     
                else: 
                    pass    
        
            break
            
        except Exception as e:
            if i == int(loop_limit):
                print("Main.py tried to read max # of times. File is corrupted. Resetting hardware_config...")
                reset_model.reset_hardware_config()
            else:
                print("Main.py tried to read while hardware_config was being written. If this continues, file is corrupted.")
                pass

#gets the mutex
def load_locks(loop_limit = 10000):
    global locks
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/configs/locks.json","r+") as l:
                locks = json.load(l) #get locks

            for k,v in locks.items():
                if locks[k] is None:
                    print("Read NoneType in locks")
                    print("Resetting locks...")
                    reset_model.reset_locks()  
                else: 
                    pass
             
            break   
    
        except Exception as e:
            if i == int(loop_limit):
                print("Tried to load lock max number of times. File is corrupted. Resetting locks...")
                reset_model.reset_locks()
            else:
                print("Main.py tried to read while locks were being written. If this continues, file is corrupted.")
                pass

#closes down a file for exclusive access
def lock(file):
    global locks
    
    with open("/home/pi/oasis-grow/configs/locks.json", "r+") as l:
        locks = json.load(l) #get lock
        
        if file == "device_state":
            locks["device_state_write_available"] = "0" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
                
        if file == "device_params":
            locks["device_params_write_available"] = "0" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()

        if file == "sensor_info":
            locks["sensor_info_write_available"] = "0" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
            
        if file == "access_config":
            locks["access_config_write_available"] = "0" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
    
        if file == "feature_toggles":
            locks["feature_toggles_write_available"] = "0" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
        
        if file == "hardware_config":
            locks["hardware_config_write_available"] = "0" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()

#releases a file from exclusive access
def unlock(file):
    global locks
    
    with open("/home/pi/oasis-grow/configs/locks.json", "r+") as l:
        locks = json.load(l) #get lock
        
        if file == "device_state":
            locks["device_state_write_available"] = "1" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
                
        if file == "device_params":
            locks["device_params_write_available"] = "1" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()

        if file == "sensor_info":
            locks["sensor_info_write_available"] = "1" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
            
        if file == "access_config":
            locks["access_config_write_available"] = "1" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
    
        if file == "feature_toggles":
            locks["feature_toggles_write_available"] = "1" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
        
        if file == "hardware_config":
            locks["hardware_config_write_available"] = "1" #let system know resource is not available
            l.seek(0)
            json.dump(locks, l)
            l.truncate()
            
#save key values to .json
def write_state(path, field, value, db_writer, loop_limit=100000): #Depends on: load_state(), 'json'; 
    if db_writer is not None: #Accepts(path, field, value, custom timeout, db_writer function); Modifies: path
        if device_state["connected"] == "1": #write state to cloud
            try:
                db_writer(access_config,field,value) #will be loaded in by listener, so is best represent change db first
            except Exception as e:
                print(e)
                pass

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke if so, 
        
        load_locks()
        
        try:
            with open(path, "r+") as x: # open the file.
                data = json.load(x) # can we load a valid json?

                if path == "/home/pi/oasis-grow/configs/device_state.json": #are we working in device_state?
                    if locks["device_state_write_available"] == "1": #check is the file is available to be written
                        lock("device_state")

                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("device_state")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/configs/device_params.json": #are we working in device_state?
                    if locks["device_params_write_available"] == "1": #check is the file is available to be written
                        lock("device_params")

                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()
            
                        unlock("device_params")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/data_out/sensor_info.json": #are we working in device_state?
                    if locks["sensor_info_write_available"] == "1": #check is the file is available to be written
                        lock("sensor_info")

                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()
            
                        unlock("sensor_info")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass

                if path == "/home/pi/oasis-grow/configs/access_config.json": #are we working in device_state?
                    if locks["access_config_write_available"] == "1": #check is the file is available to be written
                        lock("access_config")

                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("access_config")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/configs/feature_toggles.json": #are we working in device_state?
                    if locks["feature_toggles_write_available"] == "1": #check is the file is available to be written
                        lock("feature_toggles")

                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("feature_toggles")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/configs/hardware_config.json": #are we working in device_state?
                    if locks["hardware_config_write_available"] == "1": #check is the file is available to be written
                        lock("hardware_config")

                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("hardware_config")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass

        except Exception as e: #If any of the above fails:
            if i >= int(loop_limit):
                print("Tried to write state multiple times. File is corrupted. Resetting locks...")
                reset_model.reset_locks()
                reset_model.reset_device_state()
                reset_model.reset_device_params()
                break
            else:
                print(e)
                print("Resource was locked. Trying write again. If this persists, the lock file is corrupted...")
                pass #continue the loop until write is successful or ceiling is hit

#save key values to .json
def write_dict(path, dict, db_writer, loop_limit=100000): #Depends on: load_state(), dbt.patch_firebase, 'json'; Modifies: path
    
    if db_writer == False:
        #these will be loaded in by the listener, so best to make sure we represent the change in firebase too
        if device_state["connected"] == "1": #write state to cloud
            try:
                db_writer(access_config,dict)
            except Exception as e:
                print(e)
                pass

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke if so, 
        
        load_locks()
        
        try:
            with open(path, "r+") as x: # open the file.
                data = json.load(x) # can we load a valid json?

                if path == "/home/pi/oasis-grow/configs/device_state.json": #are we working in device_state?
                    if locks["device_state_write_available"] == "1": #check is the file is available to be written
                        lock("device_state")

                        data.update(dict) #write the desired values
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("device_state")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/configs/device_params.json": #are we working in device_state?
                    if locks["device_params_write_available"] == "1": #check is the file is available to be written
                        lock("device_params")

                        data.update(dict) #write the desired values
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()
            
                        unlock("device_params")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/data_out/sensor_info.json": #are we working in device_state?
                    if locks["sensor_info_write_available"] == "1": #check is the file is available to be written
                        lock("sensor_info")

                        data.update(dict) #write the desired values
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()
            
                        unlock("sensor_info")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass

                if path == "/home/pi/oasis-grow/configs/access_config.json": #are we working in device_state?
                    if locks["access_config_write_available"] == "1": #check is the file is available to be written
                        lock("access_config")

                        data.update(dict) #write the desired values
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("access_config")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/configs/feature_toggles.json": #are we working in device_state?
                    if locks["feature_toggles_write_available"] == "1": #check is the file is available to be written
                        lock("feature_toggles")

                        data.update(dict) #write the desired values
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("feature_toggles")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass
                    
                if path == "/home/pi/oasis-grow/configs/hardware_config.json": #are we working in device_state?
                    if locks["hardware_config_write_available"] == "1": #check is the file is available to be written
                        lock("hardware_config")

                        data.update(dict) #write the desired values
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        unlock("hardware_config")
                        
                        load_state()
                        break #break the loop when the write has been successful

                    else:
                        pass

        except Exception as e: #If any of the above fails:
            if i >= int(loop_limit):
                print("Tried to write state multiple times. File is corrupted. Resetting locks...")
                reset_model.reset_locks()
                reset_model.reset_device_state()
                reset_model.reset_device_params()
                break
            else:
                print(e)
                print("Resource was locked. Trying write again. If this persists, the lock file is corrupted...")
                pass #continue the loop until write is successful or ceiling is hit

#Higher-order device_state checker
def check(state, function, alt_function = None):
    load_state()
    if device_state[state] == "1":
        function()
    else:
        if alt_function is not None:
            alt_function()
        else:
            pass
