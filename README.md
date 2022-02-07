#oasis-grow

## Introduction

oasis-grow, developed by Oasis-X, is an open-source toolkit for Controlled Environment Agriculture that enables sensing, data collection, environmental control, automation, and remote monitoring applications. It is a configurable vertical farm nervous system, right out of the box. This codebase is maintained with the goal to offer the capabilities of available to everyone. Users are encouraged to contribute data, projects, and technical expertise. See [Contributing](#contributing) for details.

This repository contains:
1. Python scripts for monitoring the growing environment and interfacing with peripherals sensors and devices
2. Configuration files for grow parameters, peripheral hardware, access control, and device_state.
3. Arduino/microcontroller "minion" files for use with sensors and LEDs
4. Shell scripts for installing and configuring necessary packages

All functions can be deployed with a RaspberryPi (networking, scheduling, task management, & control) + an Arduino (precision sensors, LED management, other real-time applications). The resulting system is controllable via command line or web interface at https://dashboard.oasis-x.io

## Table of Contents

  - [Introduction](#introduction)
  - [Raspberry Pi Setup](#raspberry-pi-setup)
    - [Using pre-built image](#using-pre-built-image)
    - [Using setup scripts](#using-setup-scripts)
  - [Hardware Setup](#hardware-setup)
    - [Arduino Setup](#arduino-setup)
    - [DIY Wiring](#diy-wiring)
  - [Usage](#Usage)
    - [Button Interface](#button-interface)
  - [Configuration](#configuration)
  - [Sample Projects](#sample-projects)
  - [Contributing](#contributing)

## Raspberry Pi Setup
Users may using the [setup scripts](scripts) to build the repository and its requirements onto a fresh install of Raspbian Buster Lite (Release 05/07/2021). A pre-built image will be released alongside our next generation of devices for easier setup and deployment.

### Using Setup Scripts

Install Raspbian Lite onto your Raspberry Pi:
1. Download Raspbian Lite from [official download site](https://www.raspberrypi.org/software/operating-systems/). The firmware will not work on newer releases which utilize LibCamera instead of raspi-still.
2. Download [Balena Etcher](https://www.balena.io/etcher/).
3. Connect a microSD card to your personal computer.
4. Format the microSD card in the MS-DOS (FAT) style using your operating system's disk formatting utility.
5. Open Balena Etcher and follow the on-screen instructions to flash the image to your microSD.
6. Place the SD card into the front slot of the Raspberry Pi.
7. Connect a keyboard, monitor, and sufficient power supply to the Pi.
   
Wait for the Pi to boot, then enter the following when prompted for a username and password:
```
raspberrypi login: pi
Password: raspberry
```
When the prompt appears, enter `sudo raspi-config`. Using the arrow keys to navigate, set `Localisation Options > WLAN Country` according to your locale. Next, select `Interface Options > Camera` and turn the camera on. Finally, select `System Options > Wireless LAN` and enter the name and password for your home WiFi network.

Once you are connected to the internet, update package lists with
```
sudo apt-get update
```
Next, install git:
```
sudo apt-get install -y git
```
Use git to clone the oasis-grow repository into `/home/pi`:
```
cd /home/pi
git clone https://github.com/oasis-gardens/oasis-grow
```
Change permissions and run the `install.sh` script found in the repository's root directory. The system should reboot after this has completed.
```
chmod +x /home/pi/oasis-grow/install.sh
 . /home/pi/oasis-grow/install.sh
```

Test your build with the following. Install any modules that may have been missed during the initial setup.
```
source /home/pi/oasis-grow_venv/bin/activate
python3 /home/pi/oasis-grow/utils/unit_test.py
```

Test your build with the following. Install any modules that may have been missed during the initial setup.
```
source /home/pi/oasis-grow_venv/bin/activate
python3 /home/pi/oasis-grow/utils/unit_test.py
```

Start the grow controller during from the command line like so:
```
source /home/pi/oasis-grow_venv/bin/activate #if virtual environment not already activated
python3 /home/pi/oasis-grow/main.py run

OR

chmod +x /home/pi/oasis-grow/start.sh #if file does not already have execute permissions
. /home/pi/oasis-grow/start.sh #automatically handles virtual environment activation & run flag
```
The "run" flag after main.py starts the core controller process. This is the part of the program that ingests sensor & image data for continuous monitoring, reacts to measurements to control the environment, and communicates with the dashboard server (only if connected by the user). If main.py is executed without the "run" flag, then the controller is idle upon program startup. For example:

```
python3 /home/pi/oasis-grow/main.py
```
Launches the the button interface and networking setup, but not the core environmental controller. The only difference between these two commands is the state that our launched program starts in (run -> running (1), none -> idle (0).

If you wish to run the program automatically at startup, please execute the setup_rclocal.sh script located in oasis-grow/scripts.
```
cd /home/pi/oasis-grow/scripts
chmod +x setup_rclocal.sh
 . setup_rclocal.sh
 sudo reboot
```

When the system reboots automatically, everything should be fully functional and running in the background. We will be adding an API soon to interact with the system as it runs headless. For now you can use the [button interface](#button-interface), control everything via [Oasis-x Dashboard](https//:dashboard.oasis-x.io), or turn the core controller on-and-off by changing the "running" parameter from 0 to 1 in /home/pi/oasis-grow/configs/device_state.json. Yyou can also change the growth parameters by editing /home/pi/oasis-grow/configs/grow_params.json 

Lastly, make sure to set your local time! If not, you may find yourself wondering why none of your timers work. 
```
timedatectl list-timezones
timedatectl set-timezone <timezone>
```


### Arduino Setup

Follow these instructions if you are using peripheral sensors or an LED indicator light.
1. Download the Arduino IDE (on your personal computer) from the [official download site](www.arduino.cc/en/software).
2. Plug the Arduino into your computer via USB.
3. Download the [Oasis_DHT22_LLS_60xLEDs.ino sketch](.ino) found in this repository and install the libraries using the Arduino IDE.
4. Verify and load the sketch onto the board.
5. Find the serial port on the Raspberry Pi.
6. Plug the Arduino into the Pi via USB.

### Hardware Setup & DIY

Capable DIY enthusiasts may follow the [prototype wiring diagram]().

Note: Assemble the AC Relay & Power Management circuit at your own risk. Wiring up alternating current from power mains is extremely dangerous, so much that a single mistake can lead to serious injury or even death! Because of this, we recommend this project for INTERMEDIATE to ADVANCED Makers only. If you or someone on your team does not have experience working with high voltage, please consult a professional electrician before doing so. Oasis-X is not liable if you hurt yourself.

We are currently developing next-generation hardware for our systems that will work out of the box, no wiring required. 

## Usage

### Button Interface

If you have followed the DIY wiring guide, the three buttons on the control interface will function as follows provided `main.py` is running (see below).

**Start/Stop Button**: starts or stops the main grow-ctrl process which modulates temperature, humidity, and airflow, cycles lighting + watering aparatuses, and takes pictures at set intervals.

**Connect Button**: launches an ad-hoc network and TCP server that is used to connect your system to the internet using the Oasis Mobile App (coming soon!). When ready to link your device, press this button, wait 15 seconds and then join the "Oasis" wifi network in your phone settings. Once this is done, return to the app, press "add device", and follow the on-screen prompt.

**Water Button**: this runs the watering pump for 60 seconds, if there is one connected. It is most useful for draining setups with bulky reservoirs and tanks via hose.

### Using the Button Interface

To use the platform with the [button interface](#button-interface) and OASIS-X app, follow the instructions immediately below. If you wish to run oasis-grow from the command line, skip to the **Using the Command Line** header. Begin by opening a terminal on the Raspberry Pi and opening `/etc/rc.local`:
```
sudo nano /etc/rc.local
```
Check the following line is present & uncommented ie. if there is a leading hashtag, remove it. If you ran the setup script with the "-b" flag or are using a pre-flashed image, this should already be done for you:
```
python3 /home/pi/oasis-grow/main.py
```
If you do not see this line, add the command to `/etc/rc.local` before the `exit 0` command. Alternatively, just run the setup_rclocal.sh setup script in /home/pi/oasis-grow/scripts. It does the same thing.


This line launches our interface script on startup which accepts button inputs, controls the growing environment, collects harvest data, and manages the optional connection process with the Oasis cloud and dashboard. This all happens on reboot, so we'll run the following command to get it up and running:
```
sudo systemctl reboot
```

Once `main.py` is running, and if wiring has been [set up correctly](#diy-wiring), the buttons can be used to control the grow environment according to the functions described [here](#button-interface).

## Configuration

oasis-grow contains two important configuration files, both located in the repository's root directory. 

`feature_toggles.json` toggles certain features on and off:
| Field | Value | Function |
| ----- | ----- | -------- |
| `temp_hum_sensor` | `0` or `1` | determines whether the program is reading temperature and humidity data | 
| `water_low_sensor` | `0` or `1` | determines whether the program is reading water level data |
| `heater` | `0` or `1` | determines whether the heater is on or off |
| `humidifier` | `0` or `1` | determines whether the watering apparatus is on or off |
| `fan` | `0` or `1` | determines whether the fan is on or off |
| `light` | `0` or `1` | determines whether the lights cycle is on or off |
| `camera` | `0` or `1` | determines whether the camera is on or off |
| `water` | `0` or `1` | determines whether the watering apparatus is on or off |
| `save_images` | `0` or `1` | determines whether the camera is saving images to a continuous feed that can be used to generate timelapses |
| `save_data` | `0` or `1` | determines whether the grow control process is logging sensor data to a `.csv` file

`grow_params.json` modifies grow parameters:
| Field | Value | Function |
| ----- | ----- | -------- |
| `target_temperature` | int 0 to 100 | sets target temperature |
| `target_humidity` | int 0 to 100 | sets target humidity |
| `time_start_light` | int 0 to 23 | hour that light turns on |
| `time_start_light` | int 0 to 23 | hour that light turns off |
| `lighting_interval` | int 0 to inf | time (s) between light mode refresh |
| `camera_interval` | int 0 to inf | time (s) between camera snapshots |
| `water_duration` | int 0 to inf | duration (s) for grow to be watered |
| `water_interval` | int 0 to inf | time (s) between each watering |
|`time_start_air` | int 0 to 23 | hour that air turns on |
| `time_start_air` | int 0 to 23 | hour that air turns off |
| `air_interval` | int 0 to inf | time (s) between air mode refresh |
| `P_temp` | int | proportional feedback response for temperature (advanced)
| `D_temp` | int | dampening feedback response for temperature (advanced)
| `P_hum` | int | proportional feedback response for humidity (advanced)
| `D_hum` | int | dampening feedback response for humidity (advanced)
| `Pt_fan` | int | proportional feedback response for fan with respect to temperature (advanced)
| `Dt_fan` | int | dampening feedback response for fan with respect to temperature (advanced)
| `Ph_fan` | int | proportional feedback response for fan with respect to humidity (advanced)
| `Dh_fan` | int | dampening feedback response for fan with respect to humidity (advanced)

## Sample Projects
Oasis-grow provides a highly modular interface with countless possible applications. Forthcoming instructions will provide detailed instructions for common projects as well as a gallery of existing oasis-x applications:
- time lapse cameras
- incubators
- mushroom growing chambers
- hydroponic gardens
- outdoor environmental monitoring
- petri desh habitats
- automated irrigation
- much more!

## Contributing
oasis-grow welcomes open-source contributors and is currently accepting pull requests. Contact hello@oasis-x.com with questions or proposals.

A wiki with additional information on building from source and the makeup of the core python scripts is in the works.

