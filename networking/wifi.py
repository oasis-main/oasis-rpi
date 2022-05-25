from subprocess import Popen
from utils import concurrent_state as cs

#reconfigures network interface, tells system to boot with Access Point, restarts
def enable_AP(): #Depends on: cs.write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should be launched on next controller startup
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","1")

    #disable WiFi, enable AP, reboot
    config_ap_dhcpcd = Popen(["sudo", "cp", "/etc/dhcpcd_AP.conf", "/etc/dhcpcd.conf"])
    config_ap_dhcpcd.wait()
    config_ap_dns = Popen(["sudo", "cp", "/etc/dnsmasq_AP.conf", "/etc/dnsmasq.conf"])
    config_ap_dns.wait()
    enable_hostapd = Popen(["sudo", "systemctl", "enable", "hostapd"])
    enable_hostapd.wait()
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])

#reconfigures network interface, tells system to boot with WiF, restarts
def enable_WiFi(): #Depends on: cs.write_state(), 'subprocess'; Modifies: device_state.json, configuration files
    #tell system that the access point should not be launched on next controller startup
    cs.write_state("/home/pi/oasis-grow/configs/device_state.json","access_point","0")

    #disable WiFi, enable AP, reboot
    config_wifi_dchpcd = Popen(["sudo", "cp", "/etc/dhcpcd_WiFi.conf", "/etc/dhcpcd.conf"])
    config_wifi_dchpcd.wait()
    config_wifi_dns = Popen(["sudo", "cp", "/etc/dnsmasq_WiFi.conf", "/etc/dnsmasq.conf"])
    config_wifi_dns.wait()
    disable_hostapd = Popen(["sudo", "systemctl", "disable", "hostapd"])
    disable_hostapd.wait()
    systemctl_reboot = Popen(["sudo", "systemctl", "reboot"])