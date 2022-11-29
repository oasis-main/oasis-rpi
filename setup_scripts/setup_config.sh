#!/bin/sh -e

echo "Creating local directories..."
mkdir /home/pi/oasis-grow/configs
mkdir /home/pi/oasis-grow/data_out
mkdir /home/pi/oasis-grow/data_out/image_feed
mkdir /home/pi/oasis-grow/data_out/sensor_feed
mkdir /home/pi/oasis-grow/data_out/resource_use
mkdir /home/pi/oasis-grow/data_out/logs

echo "Moving configuration files..."
cp /home/pi/oasis-grow/defaults/hardware_config_default_template.json /home/pi/oasis-grow/configs/hardware_config.json
cp /home/pi/oasis-grow/defaults/access_config_default_template.json /home/pi/oasis-grow/configs/access_config.json
cp /home/pi/oasis-grow/defaults/feature_toggles_default_template.json /home/pi/oasis-grow/configs/feature_toggles.json
cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/configs/device_state.json
cp /home/pi/oasis-grow/defaults/control_params_default_template.json /home/pi/oasis-grow/configs/control_params.json
cp /home/pi/oasis-grow/defaults/sensor_data_default_template.json /home/pi/oasis-grow/configs/sensor_data.json
cp /home/pi/oasis-grow/defaults/power_data_default_template.json /home/pi/oasis-grow/configs/power_data.json

#Rust will create lockfiles and entries automatically when called
#Should still leave this so Python can access a default set of values. 
#The default lockfile is good because it'll help keep track of critical sections 
echo "Creating new lock file..."
cp /home/pi/oasis-grow/defaults/locks_default_template.json /home/pi/oasis-grow/configs/locks.json
echo "Creating new signal file..."
cp /home/pi/oasis-grow/defaults/signals_default_template.json /home/pi/oasis-grow/configs/signals.json

#Deprecated
#echo "Creating placeholder image..."
#cp /home/pi/oasis-grow/defaults/default_placeholder_image.jpg /home/pi/oasis-grow/data_out/image.jpg

#Permissions for writing
sudo chmod 777 -R /home/pi/oasis-grow/data_out