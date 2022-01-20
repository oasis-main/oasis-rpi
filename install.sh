#!/bin/sh -e

chmod +x /home/pi/oasis-grow/scripts/setup_env.sh
 . /home/pi/oasis-grow/scripts/setup_env.sh
chmod +x /home/pi/oasis-grow/scripts/setup_config.sh
 . /home/pi/oasis-grow/scripts/setup_config.sh
chmod +x /home/pi/oasis-grow/scripts/setup_network.sh
 . /home/pi/oasis-grow/scripts/setup_network.sh

while getopts ":b" opt; do
    case $opt in
        b)
            echo "Adding controller bootloader..."
            chmod +x /home/pi/oasis-grow/scripts/setup_bootloader.sh
             . /home/pi/oasis-grow/scripts/setup_bootloader.sh
            
            echo "Optimizing boot time..."
            chmod +x /home/pi/oasis-grow/scripts/optimize_boot.sh
             . /home/pi/oasis-grow/scripts/optimize_boot.sh -no_bt        
            
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            ;;
    esac
done

echo "Returning to WiFi mode..."
sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf
sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf
sudo systemctl disable hostapd
sudo systemctl reboot
