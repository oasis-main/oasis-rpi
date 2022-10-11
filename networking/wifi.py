import os
import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/utils')

import rusty_pipes
from utils import concurrent_state as cs

#reconfigures network interface, tells system to boot with Access Point, restarts
def enable_AP(db_writer = None): #Depends on: cs.write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should be launched on next controller startup
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","1", db_writer)

    #disable WiFi, enable AP, reboot
    config_ap_dhcpcd = rusty_pipes.Open(["sudo", "cp", "/etc/dhcpcd_AP.conf", "/etc/dhcpcd.conf"])
    config_ap_dhcpcd.wait()
    config_ap_dns = rusty_pipes.Open(["sudo", "cp", "/etc/dnsmasq_AP.conf", "/etc/dnsmasq.conf"])
    config_ap_dns.wait()
    enable_hostapd = rusty_pipes.Open(["sudo", "systemctl", "enable", "hostapd"])
    enable_hostapd.wait()
    systemctl_reboot = rusty_pipes.Open(["sudo", "systemctl", "reboot"])
    systemctl_reboot.wait()

#reconfigures network interface, tells system to boot with WiF, restarts
def enable_WiFi(): #Depends on: cs.write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should not be launched on next controller startup
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","0", db_writer = None)

    #disable WiFi, enable AP, reboot
    config_wifi_dchpcd = rusty_pipes.Open(["sudo", "cp", "/etc/dhcpcd_WiFi.conf", "/etc/dhcpcd.conf"])
    config_wifi_dchpcd.wait()
    config_wifi_dns = rusty_pipes.Open(["sudo", "cp", "/etc/dnsmasq_WiFi.conf", "/etc/dnsmasq.conf"])
    config_wifi_dns.wait()
    disable_hostapd = rusty_pipes.Open(["sudo", "systemctl", "disable", "hostapd"])
    disable_hostapd.wait()
    systemctl_reboot = rusty_pipes.Open(["sudo", "systemctl", "reboot"])
    systemctl_reboot.wait()