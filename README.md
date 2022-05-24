### Oasis-Grow

## Introduction

Oasis-Grow, developed by Oasis-X, is an open-source toolkit for controlled environment agriculture (CEA). It is a configurable nervous system for your high-tech farm, providing sensing, data collection, environmental control, automation, and remote monitoring functionality. This codebase is maintained with the goal to offer these capabilities to everyone. Users are encouraged to contribute data, projects, and technical expertise. See [Contributing](#contributing) for details.

This repository contains:
1. Python setup_scripts for collecting environmental data, manage feedback and timer regimes, and dispatching information to the relative sources.
2. Configuration files for grow parameters, peripheral hardware, access control, and device_state
3. Arduino/microcontroller "minion" files for use with sensors and LEDs
4. Shell setup_scripts for installing and configuring necessary packages

All functions can be deployed with a RaspberryPi (networking, scheduling, task management, & control) + an Arduino (precision sensors, LED management, other real-time applications). The resulting system is controllable via command line or web interface at https://dashboard.oasis-x.io

## Quick Start

**1. Setup Rasppberry Pi**

Download 32-bit Raspberry Pi OS Lite and double click to uncompress: 
https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2022-04-07/2022-04-04-raspios-bullseye-armhf-lite.img.xz

Use Disk Utility or an equivalent tool to format a micro SD card to MS-DOS(FAT), download the Raspberry Pi Imager (https://www.raspberrypi.com/software/), open the application, and follow onscreen instructions to flash the OS image obtained in step 1. 

Connect to the Raspberry Pi via HDMI monitor & keyboard (or your preferred setup), plug it in, and log in with the default password ('pi', 'raspberry') on RPiOS Buster or set your own password (default in RPiOS Bullseye). Enter:

```
sudo raspi-config
```
- setup your internet: System Options -> Wireless LAN -> follow prompt
- setup your camera: Interface Options -> Legacy Camera  -> Yes
- (optional, recommended) security: System Options -> Password  -> follow prompt
- (optional) remote access: Interface Options -> SSH  -> Yes
- (optional) remote acess: Interface Options -> Remote GPIO  -> Enable
- (opional) on-device peripherals: Interface Options -> I2C  -> Yes  
- (opional) on-device peripherals: Interface Options -> SPI  -> Yes  

**2. Install Oasis-Grow**

Open a terminal on the pi and run, in order:

```
sudo apt-get update -y
sudo apt-get install git -y
git clone https://github.com/oasis-main/oasis-grow.git 
cd oasis-grow
. install.sh
```

To validate everything went smoothly, start the virtual env and test the main process with:

```
cd oasis-grow
. start.sh
```

If successful, the above should run a ~15-30 second setup flow that ends with a statement indicating the "core process is deactivated."

**3. Configure Microcontroller, Peripheral Devices, Activated Features, and Startup**

If you plan on using sensors, then the microcontroller (usually an arduino) should manage them and print the data it collects to serial as a dict/json, which is received by the RPi.

For example:
'''
{"temperature": "0",
"humidity": "0",
"vpd": "0",
"water_low": "0",
"co2": "0",
"lux": "0",
"ph": "0",
"soil_moisture": "0",
"tds": "0"}
'''

is a valid data format for the arduino to output. It can alo take a command from the RPi to control Neopixel LEDs as the headless status indicator. All valid measurement types can be found in the "sensor_info.json" file that was created in the "configs" folder on install.

You can configure all of this yourself, or follow these instructions and use one of our example programs in the 'minions' folder.
1. Download the Arduino IDE (on your personal computer) from the [official download site](www.arduino.cc/en/software).
2. Plug the Arduino into your personal computer via USB.
3. Select and download one of the c++ sketch folders found in the "minions" directory. The functions of each are indicated with the naming convention "Oasis_component1_component2.ino"
4. Install the required libraries using Arduino IDE or your tool of choice, the compile upload your sketch onto the board.
5. Plug the Arduino into the Pi via USB. The Pi will automatically establish a connection and communicate with the arduino on program startup.

The Oasis-Grow software is configured to use GPIO Pins for interfacing with relays and push buttons. The pin mapping is given in hardware_config.json:

'''
{"actuator_gpio_map": {
                   "heat_relay": 14,
                   "humidifier_relay": 15,
                   "fan_relay": 18,
                   "light_relay": 23,
                   "water_relay": 24,
                   "air_relay": 25,
                   "dehumidifier_relay": 8
                   },
"button_gpio_map": {
                 "start_stop_button": 17,
                 "connect_internet_button": 27,
                 "action_button": 22
                 }
}
'''

Capable makers can wire this up themselves as described in the [prototype wiring diagram](https://docs.google.com/presentation/d/1E4D3Sl3dR-raVRRaoH5YC-TudYASd4O9N7d49p5N9X8/edit?usp=sharing), or purchase specialty ready-to-go hardware from us directly.

Note: Assemble the AC Relay & Power Management circuit at your own risk. Wiring up alternating current from power mains is extremely dangerous, so much that a single mistake can lead to serious injury or even death! Because of this, we recommend this project for INTERMEDIATE to ADVANCED Makers only. If you or someone on your team does not have experience working with high voltage, please consult a professional electrician before doing so. Oasis-X is not liable if you hurt yourself.

Oasis-Grow comes with imaging capabilities that make us of the Raspberry Pi's built-in camera stack. You can view these utilities in the "imaging" folder.

Finally, edit "feature_toggles.json" in 'configs' to tell the system what capabilities you are using (and which ones you are not, as they are not set up):

'''
{"temperature_sensor": "1",
"humidity_sensor": "1",
"vpd_calculation": "1",
"water_level_sensor": "1",
"co2_sensor": "1",
"lux_sensor": "1",
"ph_sensor": "0",
"tds_sensor": "0",
"soil_moisture_sensor": "0",
"heater": "1",
"heat_pid": "1",
"humidifier": "1",
"hum_pid": "1",
"dehumidifier": "1",
"dehum_pid": "1",
"fan": "1",
"fan_pid": "1",
"light": "1",
"water": "1",
"water_pid": "1",
"air": "1",
"camera": "1",
"ndvi": "1",
"video": "0",
"audio": "0",
"save_images": "1",
"save_data": "1",
"onboard_led": "0",
"debug": "0",
"action_button": "1",
"action_water": "1",
"action_camera": "0"}
'''

Now test with

'''
cd oasis-grow
source oasis_venv_pi/bin/activate
python3 main.py run
'''

You should see the core process start and run without error, with the exception of a single python 'requests' dependency conflict. Check to make sure everything is functioning as expected.

Now that we know the main and core process can run without errors, let's create an background process to run when the Pi boots up (runs through systemd):

```
. setup_scripts/optimize_boot.sh
. setup_scripts/setup_systemd.sh
sudo reboot
```

Alternatively, use these commands (runs through rc.local):

```
. setup_scripts/optimize_boot.sh
. setup_scripts/setup_rclocal.sh
sudo reboot
```

**4. Use with Local API & Button Interface (internet not required)**

To start the core process and begin collecting data + contolling your environment, you can press the 'start_stop' button on your system.
Alternatively, open up a python3 shell in the oasis-grow directory and run:

```
import api
api.start_core()
api.stop_core()
```

You can use this api to change device settings, fetch data, and connect to the Oasis Network. To view all available features, take a look at api.py or run:
'''
import api
dir(api)
'''

**5. Use with Oasis-Network for Dashboard, Remote Monitoring, & AI (internet required)**

Press the 'connect' button on your system. Alternatively, you may open up a python3 shell in the oasis-grow directory and run:

```
import api
api.connect_device()
```

The device will reboot as an access point, at which point you may connect to the 'Oasis-X' local wifi network. The password is 'community' and can be changed by running /setup_scripts/change_local_wpa.sh

Once connected, open up a new tab and navigate to http://192.168.4.1/ Enter your oasis email, oasis password, local wifi name, local wifi password, and hit the launch button. You'll get a success message and the wifi network should dissapear within a minute

Rejoin your normal internet and go to https://dashboard.oasis-x.io/ to view and control your device.

## Sample Projects
Oasis-grow provides a highly modular interface with countless possible applications. Forthcoming instructions will provide detailed instructions for common projects as well as a gallery of existing oasis-grow applications:
- time-lapse cameras
- incubators
- mushroom growing chambers
- hydroponic gardens
- outdoor environmental monitoring
- petri desh habitats
- automated irrigation
- much more!

## Contributing
oasis-grow welcomes open-source contributors and is currently accepting pull requests. Contact hello@oasis-x.com with questions or proposals.

