## Overview

Oasis-Cpu is an open-source toolkit for IoT applications on single board computers. It is suitable for home, hobby, field, and lab use, providing sensing, data collection, environmental control, equipment automation, and remote monitoring functionality. 

This toolkit can be deployed using a RaspberryPi (for scheduling, PID control, data & networking management) + an Arduino (for real-time analog & digital sensors). 

The repository includes:
1. Python setup scripts 
2. Configuration files 
3. Arduino/microcontroller "minion" files 
4. Shell setup scripts 

You can control the active system via a web interface or manage all oasis-grow instances asynchronously through the importable python API.

## Quick-Start Guide for Raspberry Pi

1. Setup your Raspberry Pi:

```
sudo raspi-config
```

- Set up your internet: System Options -> Wireless LAN -> follow prompt
- Set up your camera: Interface Options -> Legacy Camera  -> Yes
- (Optional, recommended) security: System Options -> Password  -> follow prompt
- (Optional) remote access: Interface Options -> SSH  -> Yes
- (Optional) remote access: Interface Options -> Remote GPIO  -> Enable
- (Optional) on-device peripherals: Interface Options -> I2C  -> Yes  
- (Optional) on-device peripherals: Interface Options -> SPI  -> Yes  

2. Install Oasis-Grow:

```
sudo apt-get update -y
sudo apt-get install git -y
git clone https://github.com/oasis-main/oasis-grow.git 
cd oasis-grow
. install.sh
```

To test if the installation went smoothly:

```
cd oasis-grow
. start.sh
```

If successful, the above should run a setup flow that ends with a statement indicating the "core process is deactivated."

## Contributing

We encourage users to contribute data, projects, and technical expertise. Open-source contributors are welcome, and we are currently accepting pull requests! Contact hello@oasis-x.com with questions or proposals.
