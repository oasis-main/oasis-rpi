# oasis-grow

## Introduction

oasis-grow, developed by Oasis, is an open-source toolkit for controlled environment cultivation, remote monitoring, and data collection. It is maintained with the goal of making the capabilities of automated gardening, precision agriculture, and cell culturing available to everyone. Users are encouraged to contribute data, projects, and technical expertise. See [Contributing](#contributing) for details.

This repository contains:
1. Python scripts for monitoring the grow environment and interfacing with peripherals sensors and devices,
2. Configuration files for peripheral hardware,
3. An Arduino source file for use with sensors and LEDs,
4. Shell scripts for installing and configuring necessary packages.

All functions can be deployed with a RaspberryPi (for networking, scheduling, task management, & control) + an Arduino (for precision sensors, LED management, and other real-time applications). The resulting system is controllable via shell or web interface (currently in Beta).

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
Users have two options for install: using a pre-built image to flash oasis-grow and its requisite packages directly to an SD card, or using the [setup scripts](scripts) to build the repository and its requirements onto a fresh install of Raspbian Lite.

### Using pre-built image

Install the image onto your Raspberry Pi:
1. Download the oasis-grow image here: [NOT YET AVAILABLE].
2. Download [Balena Etcher](https://www.balena.io/etcher/).
3. Connect a microSD card to your personal computer.
4. Format the microSD card in the MS-DOS (FAT) style using your operating system's disk formatting utility.
5. Open Balena Etcher and follow the on-screen instructions to flash the image to your microSD.
6. Place the SD card into the front slot of the Raspberry Pi.
7. Connect a keyboard, monitor, and sufficient power supply to the Pi.

### Using setup scripts

Install Raspbian Lite onto your Raspberry Pi:
1. Download the latest Raspbian Lite image from the [official download site](https://www.raspberrypi.org/software/operating-systems/).
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
cd ~
sudo git clone https://github.com/oasis-gardens/oasis-grow
```
Change permissions and run the `master_setup.sh` script found in the repository's root directory. If you wish to run `controller.py` automatically at startup, at the `-b` flag.
```
cd oasis-grow
chmod +x master_setup.sh
source ./master_setup.sh -b
```
When the system reboots automatically, the button interface]() and peripheral devices should be fully functional.

Set your local time EST 
```
timedatectl list-timezones
timedatectl set-timezone <timezone>
```

## Hardware Setup

### Arduino Setup

Follow these instructions if you are using peripheral sensors or an LED indicator light.
1. Download the Arduino IDE (on your personal computer) from the [official download site](www.arduino.cc/en/software).
2. Plug the Arduino into your computer via USB.
3. Download the [.ino sketch](Oasis_AM2315_LLS_LEDs.ino) found in this repository and install the libraries using the Arduino IDE.
4. Verify and load the sketch onto the board.
5. Find the serial port on the Raspberry Pi.
6. Plug the Arduino into the Pi via USB.

### DIY Wiring

DIYers can purchase a complete PCB (currently in Beta) to get a jump on wiring or instead follow the [prototype wiring diagram](https://drive.google.com/drive/folders/1jkARU0VrMkFMp18-Fvo4N2hcPtA7zahQ?usp=sharing).

Note: We are not dedicated electrical engineers, as some of you may be able to tell from the wiring guide. If you know how to make good circuit diagrams, we could use your help, so shoot us an email!

## Usage

### Button Interface

If you have followed the DIY wiring guide, the three buttons on the control interface will function as follows provided `controller.py` is running (see below).

**Start/Stop Button**: starts or stops the main grow-ctrl process which modulates temperature, humidity, and airflow, cycles lighting + watering aparatuses, and takes pictures at set intervals.

**Connect Button**: launches an ad-hoc network and TCP server that is used to connect your system to the internet using the Oasis Mobile App (coming soon!). When ready to link your device, press this button, wait 15 seconds and then join the "Oasis" wifi network in your phone settings. Once this is done, return to the app, press "add device", and follow the on-screen prompt.

**Water Button**: this runs the watering pump for 60 seconds, if there is one connected. It is most useful for draining setups with bulky reservoirs and tanks via hose.

### Using the Button Interface

To use the platform with the [button interface](#button-interface) and OASIS app, follow the instructions immediately below. If you wish to run oasis-grow from the command line, skip to the **Using the Command Line** header. Begin by opening a terminal on the Raspberry Pi and opening `/etc/rc.local`:
```
sudo nano /etc/rc.local
```
Check the following line is present & uncommented ie. if there is a leading hashtag, remove it. If you ran the setup script with the "-b" flag or are using a pre-flashed image, this should already be done for you:
```
python3 /home/pi/grow-ctrl/controller.py
```
If you do not see this line, add the command to `/etc/rc.local` before the `exit 0` command.


This line launches our interface script on startup which accepts button inputs, controls the growing environment, collects harvest data, and manages the optional connection process with the Oasis cloud and mobile app. This all happens on reboot, so we'll run the following command to get it up and running:
```
sudo systemctl reboot
```

Once `controller.py` is running, and if wiring has been [set up correctly](#diy-wiring), the buttons can be used to control the grow environment according to the functions described [here](#button-interface).

**Using the Command Line**

oasis-grow can be run directly from the command line. This is the ideal option for those who would like to use custom interfaces and integrate their own scripts + programming (we are accepting collaborators, contributions, & pull requests! Hit us up mike@oasisregenerative.com, or see [Contributing](#contributing)). In order to do this, please obtain the required hardware running grow-ctrl as a pre-flashed image (contact us) or built from source (see below).

Start by opening a terminal and run the following command to enter the project directory:
```
cd ~/grow-ctrl
```
Running the following command to start a grow cycle with default settings. This begins the process of sensing temperature, humidity, & water level, regulating heat, humidity, airflow, light, & water, and capturing images at regular intervals.
```
python3 grow_ctrl.py main
```
To make use of the [button interface](#button-interface) for controlling the grow cycles, use this instead:
```
python3 controller.py
```
If you want to run `controller.py` automatically at startup, open `rc.local` with
```
sudo nano /etc/rc.local
```
and make sure the following line is present and uncommented:
```
python3 /home/pi/grow-ctrl/controller.py
```
Remove the leading hashtag if there is one. If you do not see this line, add the command to `/etc/rc.local` before the `exit 0` command.

Two configuration files, `grow_params.json` and `feature_toggles.json`, can be edited directly from the command line using a text editor like `nano`. More details can be found under [Configuration](#configuration).

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
| `targetT` | int 0 to 100 | sets target temperature |
| `targetH` | int 0 to 100 | sets target humidity |
| `targetL` | "on" or "off" | turns light on or off |
| `LtimeOn` | int 0 to 23 | hour that light turns on |
| `LtimeOff` | int 0 to 23 | hour that light turns off |
| `lightInterval` | int 0 to inf | time (s) between light mode refresh |
| `cameraInterval` | int 0 to inf | time (s) between camera snapshots |
| `waterMode` | "on" or "off" | turns watering apparatus on or off |
| `waterDuration` | int 0 to inf | duration (s) for grow to be watered |
| `waterInterval` | int 0 to inf | time (s) between each watering |
| `P_temp` | int | proportional feedback response for temperature (advanced)
| `D_temp` | int | dampening feedback response for temperature (advanced)
| `P_hum` | int | proportional feedback response for humidity (advanced)
| `D_hum` | int | dampening feedback response for humidity (advanced)
| `Pt_fan` | int | proportional feedback response for fan with respect to temperature (advanced)
| `Dt_fan` | int | dampening feedback response for fan with respect to temperature (advanced)
| `Ph_fan` | int | proportional feedback response for fan with respect to humidity (advanced)
| `Dh_fan` | int | dampening feedback response for fan with respect to humidity (advanced)

## Sample Projects
oasis-grow provides a highly modular interface with countless possible applications. A forthcoming wiki will provide detailed instructions for common projects as well as a gallery of existing OASIS applications:
- time lapse cameras
- incubators
- mushroom growing chambers
- hydroponic gardens
- outdoor environmental monitoring
- petri desh habitats
- automated irrigation
- much more!

## Contributing
oasis-grow welcomes open-source contributors and is currently accepting pull requests. Contact mike@oasisregenerative.com with questions or proposals.

A wiki with additional information on building from source and the makeup of the core python scripts is in the works.

