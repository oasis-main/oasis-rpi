#!/bin/sh -e

echo "Creating local directories..."

sudo mkdir /home/pi/oasis-grow/state
sudo mkdir /home/pi/oasis-grow/state/concurrency_buffers

sudo mkdir /home/pi/oasis-grow/configs

sudo mkdir /home/pi/oasis-grow/data_out
sudo mkdir /home/pi/oasis-grow/data_out/image_feed
sudo mkdir /home/pi/oasis-grow/data_out/sensor_feed
sudo mkdir /home/pi/oasis-grow/data_out/logs

echo "Moving configuration files..."

sudo cp /home/pi/oasis-grow/defaults/hardware_config_default_template.json /home/pi/oasis-grow/configs/hardware_config.json
sudo cp /home/pi/oasis-grow/defaults/access_config_default_template.json /home/pi/oasis-grow/configs/access_config.json
sudo cp /home/pi/oasis-grow/defaults/feature_toggles_default_template.json /home/pi/oasis-grow/configs/feature_toggles.json

echo "Moving state files..."

sudo cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/device_state.json
sudo cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/device_state_main.json
sudo cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/device_state_grow_ctrl.json
sudo cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/device_state_listener.json

sudo cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/grow_params.json
sudo cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/grow_params_main.json
sudo cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/grow_params_grow_ctrl.json
sudo cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/grow_params_listener.json

echo "Creating new core process log..."
sudo cp /home/pi/oasis-grow/defaults/grow_ctrl_log_default_template.json /home/pi/oasis-grow/data_out/logs/grow_ctrl_log.json


