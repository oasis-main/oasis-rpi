#import shell modules
import os
import os.path
import sys
from subprocess import Popen

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

import socket, select
from _thread import *
import json
import pickle5 as pickle

#import custom modules
import reset_model

#create a password-protected lan interface for accepting credentials
import streamlit as st

#declare state variables
device_state = None #describes the current state of the system
grow_params = None #describes the grow configuration of the system
hardware_config = None #holds hardware I/O setting & pin #s
access_config = None #contains credentials for connecting to firebase
feature_toggles = None #tells the system which features are in use

def load_state(loop_limit=100000): #Depends on: 'json'; Modifies: device_state,hardware_config ,access_config
    global device_state, feature_toggles, access_config, grow_params, hardware config

    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open("/home/pi/oasis-grow/configs/device_state.json") as d:
                device_state = json.load(d) #get device state    
                
            with open("/home/pi/oasis-grow/configs/grow_params.json") as g:
                grow_params = json.load(g) #get grow params   
                
            with open("/home/pi/oasis-grow/configs/access_config.json") as a:
                access_config = json.load(a) #get access state
                
            with open ("/home/pi/oasis-grow/configs/feature_toggles.json") as f:
                feature_toggles = json.load(f) #get feature toggles
        
            with open ("/home/pi/oasis-grow/configs/hardware_config.json") as h:
                hardware_config = json.load(h) #get hardware config
        
            break
            
        except Exception as e:
            print("Error occured while listener reading. Retrying...")

#update wpa_supplicant.conf
def modWiFiConfig(SSID, password):
    config_lines = [
    'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev',
    'update_config=1',
    'country=US',
    '\n',
    'network={',
    '\tssid="{}"'.format(SSID),
    '\tpsk="{}"'.format(password),
    '\tkey_mgmt=WPA-PSK',
    '}'
    ]

    config = '\n'.join(config_lines)
    #print(config)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "r+") as w:
        w.seek(0)
        w.write(config)
        w.truncate()

    print("WiFi configs added")

#update access_config.json
def modAccessConfig(name, e, p):
    access_config = {}
    access_config["device_name"] = str(name)
    access_config["wak"] = "AIzaSyD-szNCnHbvC176y5K6haapY1J7or8XtKc"
    access_config["e"] = str(e)
    access_config["p"] = str(p)
    access_config["refresh_token"] = " "
    access_config["id_token"] = " "
    access_config["local_id"] = " "

    with open("/home/pi/oasis-grow/configs/access_config.json", "r+") as a:
        a.seek(0)
        json.dump(access_config, a)
        a.truncate()

    print("Access configs added")

#save key values to .json
def write_state(path,field,value, loop_limit=100000): #Depends on: load_state(), patch_firebase, 'json'; Modifies: path
    load_state() 

    #We DON'T patch firebase when the listener writes, because it responsible for keeping local files up to date
    for i in list(range(int(loop_limit))): #try to load, check if available, make unavailable if so, write state if so, write availabke iff so,  
        try:
            with open(path, "r+") as x: # open the file.
                data = json.load(x) # can we load a valid json?
              
                if path == "/home/pi/oasis-grow/configs/device_state.json": #are we working in device_state?
                    if data["device_state_write_available"] == "1": #check is the file is available to be written
                        data["device_state_write_available"] = "0" #let system know resource is not available
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate() 

                        data[field] = value #write the desired value
                        data["device_state_write_available"] = "1" #let system know resource is available again 
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()
                        
                        break #break the loop when the write has been successful
                        
                    else:
                        pass                    
   
                elif path == "/home/pi/oasis-grow/configs/grow_params.json": #are we working in grow_params?
                    if data["grow_params_write_available"] == "1":
                        data["grow_params_write_available"] = "0" #let system know writer is not available
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()

                        data["grow_params_write_available"] = "1"
                        data[field] = value #write the desired value
                        x.seek(0)
                        json.dump(data, x)
                        x.truncate()
                        
                        break  #break the loop when the write has been successful

                else: #otherwise, attempt a normal write
                    data[field] = value #write the desired value
                    x.seek(0)
                    json.dump(data, x)
                    x.truncate()
                    
                    break #break the loop when the write has been successful
                    
        except Exception as e: #If any of the above fails:
            print("Tried to write while another write was occuring, retrying...")
            print(e)
            pass #continue the loop until write is successful or cieling is hit


def enable_WiFi(): #Depends on: 'subprocess'; Modifies: None
    write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","0")

    config_wifi_dchpcd = Popen("sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf", shell = True)
    config_wifi_dchpcd.wait()
    config_wifi_dns = Popen("sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf", shell = True)
    config_wifi_dns.wait()
    disable_hostapd = Popen("sudo systemctl disable hostapd", shell = True)
    disable_hostapd.wait()
    systemctl_reboot = Popen("sudo systemctl reboot", shell = True)
    systemctl_reboot.wait()

def save_creds_exit(email, password, wifi_name, wifi_pass, device_name):
    global st
    
    #place credentials in proper locations
    modWiFiConfig(wifi_name, wifi_pass)
    print("Wifi creds added")
    modAccessConfig(device_name, email, password)
    print("Access creds added")
    
    st.success("Added WiFi & access credentials to device. Please reconnect computer to internet, leave this page, and log back into https://dashboard.oasis-gardens.io. If successful, you will see the device name appear under 'Your Fleet.'")
    
    #reset_box
    reset_model.reset_device_state()

    #set new_device to "0" before rebooting
    write_state("/home/pi/oasis-grow/configs/device_state.json", "new_device", "1")

    #stand up wifi and reboot
    enable_WiFi()


if __name__ == '__main__':

    default = ""

    st.title('Oasis Device Setup')

    email = st.text_input('Oasis Email', default)

    password = st.text_input('Oasis Password', default, type="password")

    wifi_name = st.text_input('Wifi Name', default)

    wifi_pass = st.text_input('Wifi Password', default, type="password")

    device_name = st.text_input('Name this device:', default)

    #st.button('Launch', on_click=save_creds_exit, args=[email, password, wifi_name, wifi_pass, device_name]) #only for recent streamlit versions

    if st.button("Launch"):
        save_creds_exit(email, password, wifi_name, wifi_pass, device_name)
