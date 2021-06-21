echo "Adding packages..."
sudo apt install -y python3-pip
sudo apt-get install -y python3-venv
sudo apt-get install -y libopenjp2-7
sudo apt-get install -y libtiff5
sudo apt-get install -y libatlas-base-dev

echo "Creating virtual environment..."
python3 -m venv /home/pi/oasis-grow
source /home/pi/oasis-grow/bin/activate

echo "Configuring PATH variable..."
echo "export PATH=\"home/pi/.local/bin:$PATH" | sudo tee -a /home/pi/.bashrc
source /home/pi/.bashrc

echo "Installing modules..."
pip3 install -r /home/pi/oasis-grow/requirements.txt

echo "Installing dependencies..."
sudo apt install -y hostapd
sudo apt install -y dnsmasq

echo "Configuring services..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo rfkill unblock wlan

echo "Creating backups..."
sudo cp /etc/dhcpcd.conf /etc/dhcpcd_backup.conf
sudo cp /etc/dnsmasq.conf /etc/dnsmasq_backup.conf
sudo cp /etc/network/interfaces /etc/network/interfaces_backup

echo "Writing configurations..."
printf "
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
" | sudo tee -a /etc/dhcpcd.conf
printf "
#Listening interface
interface=wlan0
#Pool of IP addresses served via DHCP
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
#Local wireless DNS domain
domain=wlan
#Alias for this router
address=/gw.wlan/192.168.4.1
" | sudo tee -a /etc/dnsmasq.conf
printf "
country_code=US
interface=wlan0
ssid=Oasis
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
" | sudo tee -a /etc/hostapd/hostapd.conf

echo "Staging config files for network mode switching..."
sudo cp /etc/dhcpcd.conf /etc/dhcpcd_AP.conf
sudo cp /etc/dhcpcd_backup.conf /etc/dhcpcd_WiFi.conf
sudo cp /etc/dnsmasq.conf /etc/dnsmasq_AP.conf
sudo cp /etc/dnsmasq_backup.conf /etc/dnsmasq_WiFi.conf

echo "Creating data directories..."
mkdir /home/pi/logs
mkdir /home/pi/data_output
mkdir /home/pi/data_output/image_feed
mkdir /home/pi/data_output/sensor_feed

echo "Moving configuration files..."
cp /home/pi/oasis-grow/hardware_config_default_template.json /home/pi/hardware_config.json
cp /home/pi/oasis-grow/access_config_default_template.json /home/pi/access_config.json
cp /home/pi/oasis-grow/device_state_default_template.json /home/pi/device_state.json
cp /home/pi/oasis-grow/device_state_default_template.json /home/pi/device_state_buffer.json
cp /home/pi/oasis-grow/grow_params_default_template.json /home/pi/grow_params.json
cp /home/pi/oasis-grow/grow_params_default_template.json /home/pi/grow_params_buffer.json
cp /home/pi/oasis-grow/feature_toggles_default_template.json /home/pi/feature_toggles.json
cp /home/pi/oasis-grow/growCtrl_log_default_template.json /home/pi/logs/growCtrl_log.json
