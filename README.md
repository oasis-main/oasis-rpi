[UNDER DEVELOPMENT]

# What is grow-ctrl?

grow-ctrl, developed by OASIS, is an open toolkit for controlled environment culturing, remote monitoring, and data collection. It is maintained with the goal of making the capabilities of automated gardening, precision agriculture, and cell culturing available to everyone. All functions can be accomplished with a RaspberryPi + Arduino and the requisite peripheral hardware. The software interfaces a sensor array, camera, and appliance set and is controllable via shell or mobile app (currently in Beta).      
# Hardware Setup

DIYers can purchase a complete PCB (currently in Beta) to get a jump on wiring or instead follow the prototype wiring diagram available here: https://docs.google.com/spreadsheets/d/e/2PACX-1vQgn0rGJVujcdRgQUK21jd7PybuvJZdb9DuSV6mf8QKvGKiNE8npMvLlrqJvNgFDA/pubhtml

# Software Setup (Raspberry Pi)

First, flash Raspian to an SD card, insert it into the board, and plug in the power
(NOTE: the SD card is what is used as the memory of your pi and will hold program code and boot instructions. Using a higher quality one and shutting down the pi properly  will increase the stability of Oasis) 
  
  1. Download Balena Etcher: https://www.balena.io/etcher/
  
  2. Download the latest Raspberry Pi Operating System: https://howtoraspberrypi.com/downloads/
  
  3. Connect a micro-SD card to your personal computer
  
  3. Format the micro-SD in the MS-DOS (FAT) style. This will be done differently depending on the operating system of your personal computer. 
  With MacOS, it is done using disk utility
  
  4. Open up balena etcher, follow onscreen instructions to flash the RasPi OS to the SD, will eject automatically when finished
  
  5. Place the SD card into the front slot of the Raspberry Pi
  
  6. Connect a keyboard and monitor to the board via USB
  
  7. Power up, and follow the on-screen setup guide
     - select languages & timezone
     - connect WiFi
     - update software

Now we will install the grow-ctrl software onto the Pi. This is where we will start working from the terminal, so open up a new window

1. Remove unnecessary software
    Raspbian comes with a package called ‘GVfs’ (GNOME virtual file system). It does not do much and causes a lot of kernel panics (crashes)
      sudo apt-get purge --auto-remove gvfs-backends gvfs-fuse

Clone the grow-ctrl repository
    cd ~
    git clone https://github.com/OasisRegenerative/grow-ctrl.git
    cd grow-ctrl
  Install dependencies & change settings
    pip3 install subprocess32 firebase pyrebase python_jwt gcloud sseclient requests-toolbelt pickle5
    sudo raspi-config
      Interface
        Enable camera
        Enable remote GPIO
        Enable SSH
  Setup launcher script
    cd grow-ctrl
    chmod 775 launcher.sh
    cd # return home
    mkdir logs
    nano ~/logs/growCtrl_log.json 
    sudo crontab -e
    @reboot sh /home/pi/grow-ctrl/launcher.sh >/home/pi/logs/cronlog 2>&1
  
  Test
    sudo reboot
    cd logs
    cat cronlog

  Setup Networking Protocol
  Resources:
    https://www.lifewire.com/what-is-dhcp-2625848
    https://en.wikipedia.org/wiki/Hostapd
    https://en.wikipedia.org/wiki/Wireless_access_point
    http://www.thekelleys.org.uk/dnsmasq/doc.html
  Tip Make a backup of config files with “sudo cp”
    sudo cp /etc/network/interfaces /etc/network/interfaces-backup
  Tip If you had previous config files and made a backup you can restore your original with the command “sudo mv”:
    sudo mv /etc/network/interfaces-backup /etc/network/interfaces
  Set up access-point: https://www.raspberrypi.org/documentation/configuration/wireless/access-point-routed.md
    sudo apt install hostapd
    sudo systemctl unmask hostapd
    sudo systemctl enable hostapd
    sudo apt install dnsmasq
    sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
    sudo cp /etc/dhcpcd.conf /etc/dhcpcd_backup.conf
    sudo nano /etc/dhcpcd.conf
        Go to the end of the file and add the following:
            interface wlan0
            static ip_address=192.168.4.1/24
            nohook wpa_supplicant
    sudo mv /etc/dnsmasq.conf /etc/dnsmasq_backup.conf
    sudo nano /etc/dnsmasq.conf
      Add the following to the file and save it:
          # Listening interface
          interface=wlan0 
          # Pool of IP addresses served via DHCP
          dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
          # Local wireless DNS domain
          domain=wlan     
          # Alias for this router
          address=/gw.wlan/192.168.4.1
    sudo rfkill unblock wlan
    sudo nano /etc/hostapd/hostapd.conf
       Add the information below to the configuration file. This configuration assumes we are using channel 7, with a network name of NameOfNetwork, 
       and a password AardvarkBadgerHedgehog. Note that the name and password should not have quotes around them. 
       The passphrase should be between 8 and 64 characters in length.
          country_code=GB
          interface=wlan0
          ssid=NameOfNetwork
          hw_mode=g
          channel=7
          macaddr_acl=0
          auth_algs=1
          ignore_broadcast_ssid=0
          wpa=2
          wpa_passphrase=AardvarkBadgerHedgehog
          wpa_key_mgmt=WPA-PSK
          wpa_pairwise=TKIP
          rsn_pairwise=CCMP
      Note the line country_code=GB: it configures the computer to use the correct wireless frequencies in the United Kingdom. 
      Adapt this line and specify the two-letter ISO code of your country. See Wikipedia for a list of two-letter ISO 3166-1 country codes.

      To use the 5 GHz band, you can change the operations mode from hw_mode=g to hw_mode=a. Possible values for hw_mode are:
      a = IEEE 802.11a (5 GHz)
      b = IEEE 802.11b (2.4 GHz)
      g = IEEE 802.11g (2.4 GHz)
      ad = IEEE 802.11ad (60 GHz)
      sudo systemctl reboot

  Access point should be discoverable on development machine
  Join ssid using passkey through wifi interface
  Test connection with
    ssh pi@192.168.4.1

  Stage config files for network mode switching
    sudo cp /etc/dhcpcd.conf /etc/dhcpcd_AP.conf
    sudo cp /etc/dhcpcd_backup.conf /etc/dhcpcd_WiFi.conf
    sudo cp /etc/dnsmasq.conf /etc/dnsmasq_AP.conf
    sudo cp /etc/dnsmasq_backup.conf /etc/dnsmasq_WiFi.conf
  
  Note: Series of Commands to Launch in Access Point Mode
    sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf
    sudo cp /etc/dnnanosmasq_AP.conf /etc/dnsmasq.conf
    sudo systemctl enable hostapd
  
  Note: Series of Commands to Launch in Wifi Mode
    sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf
    sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf
    sudo systemctl disable hostapd
    sudo systemctl reboot
 

  setup configuration files
    cp hardware_config_default_template.json /home/pi/hardware_config.json
    cp access_config_default_template.json /home/pi/access_config.json
    cp device_state_default.json /home/pi/device_state.json

Arduino Software Setup:
  Download the official arduino IDE for your preferred operating system. We recommend doing this on Mac or PC and not on the Raspberry Pi itself
  Plug the arduino into your computer via USB
  Download the .ino sketch from this Github, install libraries using the Arduino IDE
  Verify and load the sketch onto the board
  Find the serial port on raspberry pi
  Plug in arduino to pi via usb
  Open terminal, run:
    ls /dev/tty*
  You should see the port which the arduino is plugged into
  To determine which port it actually, unplug the arduino and run the command again, see which ones appear and disappear
   Copy the serial port ID in quotes to the python scripts (in this case, controller_daemon, oasis_server.py, & sensing_feedback_v1.11.py) serial.Serial(‘your port’,9600) 

Start Grow Cycle from the Command Line:
  The latest grow-cycle program (which keeps the environment steady, does actions on timers, and collects data) is titled "sensingfeedback_v.X.X.py"
  To run it, open the terminal and
    cd ~/grow-ctrl
    python3 sensingfeedback_vX.X.py main

Using the Button Interface:
[coming soon]

Connect to Mobile App:

[coming soon]



