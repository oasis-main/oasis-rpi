#!/bin/sh -e

echo "Creating local directories..."

mkdir /home/pi/oasis-grow/state

mkdir /home/pi/oasis-grow/configs

mkdir /home/pi/oasis-grow/data-out
mkdir /home/pi/oasis-grow/data-out/image_feed
mkdir /home/pi/oasis-grow/data-out/sensor_feed
mkdir /home/pi/oasis-grow/data-out/logs

echo "Moving configuration files..."

cp /home/pi/oasis-grow/defaults/hardware_config_default_template.json /home/pi/oasis-grow/configs/hardware_config.json
cp /home/pi/oasis-grow/defaults/access_config_default_template.json /home/pi/oasis-grow/configs/access_config.json
cp /home/pi/oasis-grow/defaults/feature_toggles_default_template.json /home/pi/oasis-grow/configs/feature_toggles.json

echo "Moving state files..."

cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/device_state.json
cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/device_state_main.json
cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/device_state_grow_ctrl.json
cp /home/pi/oasis-grow/defaults/device_state_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/device_state_listener.json

cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/grow_params.json
cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/grow_params_main.json
cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/grow_params_grow_ctrl.json
cp /home/pi/oasis-grow/defaults/grow_params_default_template.json /home/pi/oasis-grow/state/concurrency_buffers/grow_params_listener.json

cp /home/pi/oasis-grow/defaults/grow_ctrl_log_default_template.json /home/pi/oasis-grow/data_out/logs/grow_ctrl_log.json
