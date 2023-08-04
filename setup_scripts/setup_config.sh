#!/bin/sh -e

echo "Creating local directories..."
mkdir /home/pi/oasis-cpu/configs
mkdir /home/pi/oasis-cpu/data_out
mkdir /home/pi/oasis-cpu/data_out/image_feed
mkdir /home/pi/oasis-cpu/data_out/sensor_feed
mkdir /home/pi/oasis-cpu/data_out/resource_use
mkdir /home/pi/oasis-cpu/data_out/logs

echo "Moving configuration files..."
cp /home/pi/oasis-cpu/defaults/hardware_config_default_template.json /home/pi/oasis-cpu/configs/hardware_config.json
cp /home/pi/oasis-cpu/defaults/access_config_default_template.json /home/pi/oasis-cpu/configs/access_config.json
cp /home/pi/oasis-cpu/defaults/feature_toggles_default_template.json /home/pi/oasis-cpu/configs/feature_toggles.json
cp /home/pi/oasis-cpu/defaults/device_state_default_template.json /home/pi/oasis-cpu/configs/device_state.json
cp /home/pi/oasis-cpu/defaults/control_params_default_template.json /home/pi/oasis-cpu/configs/control_params.json
cp /home/pi/oasis-cpu/defaults/sensor_data_default_template.json /home/pi/oasis-cpu/configs/sensor_data.json
cp /home/pi/oasis-cpu/defaults/power_data_default_template.json /home/pi/oasis-cpu/configs/power_data.json

#Rusty Pipes will create lockfiles and entries automatically when called
#Should still leave the config setup here so Python can access a default set of keys+values. 
#The default lockfile is good because it'll help keep track of critical sections 
echo "Creating new lock file..."
cp /home/pi/oasis-cpu/defaults/locks_default_template.json /home/pi/oasis-cpu/configs/locks.json
echo "Creating new signal file..."
cp /home/pi/oasis-cpu/defaults/signals_default_template.json /home/pi/oasis-cpu/configs/signals.json

#Permissions for writing
sudo chmod 777 -R /home/pi/oasis-cpu/data_out