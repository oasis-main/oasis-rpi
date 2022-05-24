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
import concurrent_state as cs
import wifi

#create a password-protected lan interface for accepting credentials
import streamlit as st

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
    cs.access_config = {}
    cs.access_config["device_name"] = str(name)
    cs.access_config["wak"] = "AIzaSyBPuJwU--0ZlvsbDV9LmKJdYIljwNwzmVk"
    cs.access_config["e"] = str(e)
    cs.access_config["p"] = str(p)
    cs.access_config["refresh_token"] = " "
    cs.access_config["id_token"] = " "
    cs.access_config["local_id"] = " "

    with open("/home/pi/oasis-grow/configs/access_config.json", "r+") as a:
        a.seek(0)
        json.dump(cs.access_config, a)
        a.truncate()

    print("Access configs added")

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
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "new_device", "1", offline_only=True)

    #stand up wifi and reboot
    wifi.enable_WiFi()


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
