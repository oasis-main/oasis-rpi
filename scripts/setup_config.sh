echo "Moving configuration files..."
cd oasis-grow
cp oasis-grow/hardware_config_default_template.json /home/pi/hardware_config.json
cp oasis-grow/access_config_default_template.json /home/pi/access_config.json
cp oasis-grow/device_state_default_template.json /home/pi/device_state.json
cp oasis-grow/device_state_default_template.json /home/pi/device_state_buffer.json
cp oasis-grow/grow_params_default_template.json /home/pi/grow_params.json
cp oasis-grow/grow_params_default_template.json /home/pi/grow_params_buffer.json
cp oasis-grow/feature_toggles_default_template.json /home/pi/feature_toggles.json
mkdir /home/pi/logs
cp growCtrl_log_default_template.json /home/pi/logs/growCtrl_log.json
