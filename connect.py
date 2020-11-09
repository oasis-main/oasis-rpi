#import packages
import os
import time

def WiFidownAPup():
    os.system("sudo ifconfig wlan0 down")
    os.system("sudo systemctl stop hostapd")
    os.system("sudo systemctl stop dhcpcd")
    os.system("sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf")
    os.system("sudo cp /etc/dnsmasq_AP.conf /etc/dnsmasq.conf")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo rfkill unblock wlan")
    os.system("sudo systemctl unmask hostapd")
    os.system("sudo systemctl start hostapd")
    os.system("sudo systemctl restart dhcpcd")
    os.system("sudo ifconfig wlan0 up")

def APdownWiFiup():
    os.system("sudo ifconfig wlan0 down")
    os.system("sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf")
    os.system("sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo systemctl restart dhcpcd")
    os.system("sudo ifconfig wlan0 up")

#WiFidownAPup()
APdownWiFiup()
