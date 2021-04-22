# What is grow-ctrl?

grow-ctrl, developed by OASIS, is an open toolkit for controlled environment cultivation, remote monitoring, and data collection. It is maintained with the goal of making the capabilities of automated gardening, precision agriculture, and cell culturing available to everyone. All functions can be accomplished with a RaspberryPi + Arduino and the requisite peripheral hardware. The software interfaces a sensor array, camera, and appliance set and is controllable via shell or mobile app interface (currently in Beta).     

# Get started with a pre-built image

Download our grow-ctrl image to get started right away! Available here: https://drive.google.com/drive/folders/1bbqZBXVvcPGmtm_TweJJgc5ww8IDLcl-?usp=sharing

Setup:
  1. Download Balena Etcher: https://www.balena.io/etcher/
  
  2. Connect a micro-SD card to your personal computer
  
  3. Format the micro-SD in the MS-DOS (FAT) style. This will be done differently depending on the operating system of your personal computer. 
  With MacOS, it is done using disk utility
  
  4. Open up balena etcher, follow onscreen instructions to flash the grow-ctrl image to the SD, will eject automatically when finished
  
  5. Place the SD card into the front slot of the Raspberry Pi
  
  6. Connect a keyboard and monitor to the board via USB. Proceeed to instructions in the text below.

Note: You'll still have to configure wifi and flash the Adruino code to use the full set of features.

# Instructions for Use

**Using with Interface:**

To use the platform with the button interface and Oasis App, make sure you have a Raspberry Pi, Arduino, and related hardware running a pre-flashed debian image (see above) or grow-ctrl software built from source (see below).

Power on the Raspberry pi, open a terminal and run:

    sudo nano /etc/rc.local

Go to the bottom of the file and uncomment (remove the hashtag at the beginning of) the following lines:

    #sudo python3 /home/pi/grow-ctrl/controller.py

This line launches our interface script on startup which accepts button inputs, controls the growing environment, collects harvest data, and manages the optional connection process with the Oasis cloud and mobile app. This all happens on reboot, so we'll run the following command to get it up and running:

    sudo reboot

Whether you are using OASIS hardware (coming soon) or followed the DIY wiring guide (see below), you will likely have noticed three buttons in the control interface. Here is what they are and how to use them:

    1. Start/Stop Button: starts or stops the main grow-ctrl process which modulates temperature, humidity, and airflow, cycles lighting + watering aparatuses, and takes pictures at set intervals.  

    2. Connect Button: launches an ad-hoc network and TCP server that is used to connect your system to the internet using the Oasis Mobile App (coming soon!). When ready to link your device, press this button, wait 15 seconds and then join the "Oasis" wifi network in your phone settings. Once this is done, return to the app, press "add device", and follow the on-screen prompt.

    3. Water Button: this runs the watering pump for 60 seconds, if there is one connected. It is most useful for draining setups with bulky reservoirs and tanks via hose.      

**Using the Command Line:**

grow-ctrl can be run directly from the command line. This is the ideal option for those who would like to use custom interfaces and integrate their own scripts + programming (we are accepting collaborators, contributions, & pull requests! Hit us up mike@oasisregenerative.com). In order to do this, please obtain the required hardware running grow-ctrl as a pre-flashed image (contact us) or built from source (see below).

Start by opening a terminal and run the following command to enter the project directory:

    cd ~/grow-ctrl

Running the following command to start a grow cycle with default settings. This begins the process of sensing temperature, humidity, & water level, regulating hea, humidity, airflow, light, & water, and capturing images at regular intervals.

    sudo python3 grow_ctrl.py main

To make use of the button interface for controlling the grow cycles, use this instead: 

    sudo python3 controller.py

To start either the button controller interface at startup, run:

    sudo nano /etc/rc.local
    
and uncomment the following line:

    ##sudo python3 /home/pi/grow-ctrl/controller.py

You can edit the launcher.sh script to lauch either controller.py (button interface), or grow_ctrl.py main (raw grow process manager). 

To customize our setup and growing environment, we can run:

    cd ~
    nano grow_params.json

to modify grow parameters, and

    cd ~
    nano feature_toggles.json

to toggle certain features on and off. The other two config files, access_config.json and device_state.json, are of little concern as they are used primarily by the Oasis interface. These are normally managed prior to distribution and through our app interface, but here is a description of the variables in each of these files and what purpose they serve if seeking to modify from the command line:

    #grow_params.json
    "targetT": integer 0 to 100, sets the target temperature
    "targetH": integer 0 to 100, sets the target humidity
    "targetL": "on" or "off", determined whether the light will work
    "LtimeOn": integer 0 to 23, hour that the lights turn on
    "LtimeOff": integer 0 to 23, hour that the lights turn off
    "lightInterval": integer 0 to inf, time in seconds between refreshing the light mode
    "cameraInterval": integer 0 to inf, time in seconds between camera snapshots
    "waterMode": "on" or "off, determines whether the watering aparatus is in use
    "waterDuration": integer 0 to inf, specifies how long in seconds the grow should be watered
    "waterInterval": integer 0 to inf, specified how long in seconds between each watering
    "P_temp": integer, proportional feedback response for temperature (advanced)
    "D_temp": integer, dampening feedback response for temperature (advanced)
    "P_hum": integer, dampening feedback response for humidity (advanced)
    "D_hum": integer, proportional feedback response for humidity (advanced)
    "Pt_fan": integer, proportional feedback response for fan with respect to temperature (advanced)
    "Dt_fan": integer, dampening feedback response for fan with respect to temperature (advanced)
    "Ph_fan": integer, proportional feedback response for fan with respect to humidity (advanced)
    "Dh_fan": integer, dampening feedback response for fan with respect to humidity (advanced)

    #feature_toggles.json
    temp_hum_sensor: "0" or "1", determines whether the program is reading temperature and humidity data 
    water_low_sensor: "0" or "1", determines whether the program is reading water level data
    heater: "0" or "1", determines whether the heater is on or off
    humidifier: "0" or "1", determines whether the watering aparatus is on or off
    fan: "0" or "1", determines whether the fan is on or off
    light: "0" or "1", determines whether the lights cycle is on or off
    camera: "0" or "1", determines whether the camera is on or off
    water: "0" or "1", determines whether the watering aparatus is on or off
    save_images: "0" or "1", determines whether the camera is saving images to a continuous feed that can be used to generate timelapses
    save_data: "0" or "1", determines whether the grow control process is logging sensor data to a .csv file

To save parameters to these files in Nano, press Ctrl+X and then Y to save & exit.

If using a pre-built image, you can connect your device to wifi by running:

    cd grow-ctrl
    sudo python3
    from oasis_server import modWiFiConfig
    modWiFiConfig("your network name","your network password")
    exit()
    sudo reboot

Alternatively, you can add your credentials to the /etc/wpa_supplicant/wpa_supplicant.conf file and reboot.

# Arduino Setup (necessary if using sensors & indicator LED):
  
1. Download the official arduino IDE for your preferred operating system. We recommend doing this on Mac or PC and not on the Raspberry Pi itself

2. Plug the arduino into your computer via USB

3. Download the .ino sketch from this Github, install libraries using the Arduino IDE

4. Verify and load the sketch onto the board

5. Find the serial port on raspberry pi

6. Plug in arduino to pi via usb

# DIY Hardware Setup

DIYers can purchase a complete PCB (currently in Beta) to get a jump on wiring or instead follow the prototype wiring diagram available here: https://drive.google.com/drive/folders/1jkARU0VrMkFMp18-Fvo4N2hcPtA7zahQ?usp=sharing

Note: We are not dedicated electrical engineers, as some of you may be able to tell from the wiring guide. If you know how to make good circuit diagrams, we could use your help, so shoot us an email!

# Build Raspberry Pi from Source

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

Now we will install the grow-ctrl software and configure the pi to run it. This is where we will start working from the terminal, so open up a new window.

1. Upgrade the RaspPi OS and software packages by running

       sudo apt-get update
       sudo apt-get upgrade

2. Remove unnecessary software
   - Raspbian comes with a package called ‘GVfs’ (GNOME virtual file system). It does not do much and causes a lot of kernel panics (crashes)

         sudo apt-get purge --auto-remove gvfs-backends gvfs-fuse

2. Clone the grow-ctrl repository

       cd ~
       git clone https://github.com/OasisRegenerative/grow-ctrl.git
       cd grow-ctrl

3. Install dependencies & change settings
       
       pip3 install subprocess32 firebase pyrebase python_jwt gcloud sseclient requests-toolbelt pickle5
       sudo raspi-config
       - Interface
          - Enable camera

3. Setup launcher and listener script (This is only required if you intend to launch the program at startup, in conjunction with the mobile interface)

       cd grow-ctrl
       chmod 775 launcher.sh
       chmod 775 listener.sh
       cd # return home
       mkdir logs
       nano ~/logs/growCtrl_log.json 

    - Use cron to make the launcher and listener scripts initialize at reboot.

          sudo crontab -e
      - Add the following lines to this file, then exit by hitting ctrl+x, Y, enter

            @reboot sh /home/pi/grow-ctrl/launcher.sh >/home/pi/logs/cronlog_launcher 2>&1
            @reboot sh /home/pi/grow-ctrl/listener.sh >/home/pi/logs/cronlog_listener 2>&1
  
     - To launch, test, and debug the startup script, run:

           sudo reboot
           cd logs
           cat cronlog_launcher
           cat cronlog_listener
           cat growCtrl_log.json

4. If you plan on connecting to a mobile or desktop interface to remotely monitor your grow, follow these steps to set up access point networking. This will allow user and network credentials to be passed from your device to the grow-ctrl node
   - Tip: Make a backup of config files with “sudo cp”

          sudo cp /etc/network/interfaces /etc/network/interfaces-backup

  - Tip If you had previous config files and made a backup you can restore your original with the command “sudo mv”:

          sudo mv /etc/network/interfaces-backup /etc/network/interfaces

  - Set up access-point:

        sudo apt install hostapd
        sudo systemctl unmask hostapd
        sudo systemctl enable hostapd
        sudo apt install dnsmasq
        sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
        sudo cp /etc/dhcpcd.conf /etc/dhcpcd_backup.conf
        sudo nano /etc/dhcpcd.conf 

       - Go to the end of the file and   add the following:
       
             interface wlan0
             static ip_address=192.168.4.1/24
             nohook wpa_supplicant

        sudo mv /etc/dnsmasq.conf /etc/dnsmasq_backup.conf
        sudo nano /etc/dnsmasq.conf
       - Add the following to the file and save it:

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
       - Add the information below to the configuration file. This configuration assumes we are using channel 7, with a network name of NameOfNetwork, 
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
       - Note the line country_code=GB: it configures the computer to use the correct wireless frequencies in the United Kingdom. 
       Adapt this line and specify the two-letter ISO code of your country. See Wikipedia for a list of two-letter ISO 3166-1 country codes.

       To use the 5 GHz band, you can change the operations mode from hw_mode=g to hw_mode=a. Possible values for hw_mode are:
       a = IEEE 802.11a (5 GHz)
       b = IEEE 802.11b (2.4 GHz)
       g = IEEE 802.11g (2.4 GHz)
       ad = IEEE 802.11ad (60 GHz)
      
       - For these changes to take effect, run: 
       
             sudo systemctl reboot

  
      - Access point should be discoverable on development machine. Test connection with

             ssh pi@192.168.4.1

      - Stage config files for network mode switching
    
            sudo cp /etc/dhcpcd.conf /etc/dhcpcd_AP.conf
            sudo cp /etc/dhcpcd_backup.conf /etc/dhcpcd_WiFi.conf
            sudo cp /etc/dnsmasq.conf /etc/dnsmasq_AP.conf
            sudo cp /etc/dnsmasq_backup.conf /etc/dnsmasq_WiFi.conf
  
      - Note: Series of Commands to Launch in Access Point Mode
    
            sudo cp /etc/dhcpcd_AP.conf /etc/dhcpcd.conf
            sudo cp /etc/dnnanosmasq_AP.conf /etc/dnsmasq.conf
            sudo systemctl enable hostapd
            sudo systemctl reboot
  
      - Note: Series of Commands to Launch in Wifi Mode

            sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf
            sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf
            sudo systemctl disable hostapd
            sudo systemctl reboot

5. Finally, we copy our configuration files into the root directory where they can be accessed by our programs

            cd grow-ctrl
            cp hardware_config_default_template.json /home/pi/hardware_config.json
            cp access_config_default_template.json /home/pi/access_config.json
            cp device_state_default.json /home/pi/device_state.json
            cp device_state_default.json /home/pi/device_state_buffer.json
            cp grow_params_default_template.json /home/pi/grow_params.json
            cp grow_params_default_template.json /home/pi/grow_params_buffer.json
            cp growCtrl_log_default.json /home/pi/logs/growCtrl_log.json
            cp feature_toggles_default_template.json /home/pi/feature_toggles.json
 




