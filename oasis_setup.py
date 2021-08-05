#import shell modules
import os
import os.path
import sys
from subprocess import Popen
import reset_model

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
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

#create a secure lan interface for accepting credentials
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
    access_config = {}
    access_config["device_name"] = str(name)
    access_config["wak"] = "AIzaSyD-szNCnHbvC176y5K6haapY1J7or8XtKc"
    access_config["e"] = str(e)
    access_config["p"] = str(p)
    access_config["refresh_token"] = " "
    access_config["id_token"] = " "
    access_config["local_id"] = " "

    with open("/home/pi/access_config.json", "r+") as a:
        a.seek(0)
        json.dump(access_config, a)
        a.truncate()

    print("Access configs added")

def write_state(path,field,value): #Depends on: load_state(), 'json'; Modifies: path

    with open(path, "r+") as x: #write state to local files
        data = json.load(x)
        data[field] = value
        x.seek(0)
        json.dump(data, x)
        x.truncate()

def enable_WiFi(): #Depends on: 'subprocess'; Modifies: None
    config_wifi_dchpcd = Popen("sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf", shell = True)
    config_wifi_dchpcd.wait()
    config_wifi_dns = Popen("sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf", shell = True)
    config_wifi_dns.wait()
    disable_hostapd = Popen("sudo systemctl disable hostapd", shell = True)
    disable_hostapd.wait()
    systemctl_reboot = Popen("sudo systemctl reboot", shell = True)
    systemctl_reboot.wait()

def save_creds_exit(email, password, wifi_name, wifi_pass, device_name):
    #place credentials in proper locations
    modWiFiConfig(wifi_name, wifi_pass)
    print("Wifi creds added")
    modAccessConfig(device_name, email, password)
    print("Access creds added")

    #reset_box
    reset_model.reset_device_state()

    #set AccessPoint state to "0" before rebooting
    write_state("/home/pi/device_state.json", "new_device", "1")

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
