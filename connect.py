#import packages
import os
import time

#WiFi down, AP up
os.system("sudo ifconfig wlan0 down")
time.sleep(1)
os.system("sudo systemctl stop hostapd")
time.sleep(1)
os.system("sudo systemctl stop dhcpcd")
time.sleep(1)
os.system("sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf")
time.sleep(1)
os.system("sudo cp /etc/dnsmasq_AP.conf /etc/dnsmasq.conf")
time.sleep(1)
os.system("sudo systemctl daemon-reload")
time.sleep(1)
os.system("sudo rfkill unblock wlan")
time.sleep(1)
os.system("sudo systemctl unmask hostapd")
time.sleep(1)
os.system("sudo systemctl start hostapd")
time.sleep(1)
os.system("sudo systemctl restart dhcpcd")
time.sleep(1)
os.system("sudo ifconfig wlan0 up")

#keep AP up for 75 seconds (15 to join the network, 60 to connect)
time.sleep(75)

#AP down, WiFi up
os.system("sudo ifconfig wlan0 down")
os.system("sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf")
os.system("sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf")
os.system("sudo systemctl daemon-reload")
os.system("sudo systemctl restart dhcpcd")
os.system("sudo ifconfig wlan0 up")

