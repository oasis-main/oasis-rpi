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

echo "Returning to WiFi mode..."
sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf
sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf
sudo systemctl disable hostapd
sudo systemctl reboot
