#!/bin/sh -e

sudo chmod +x /home/pi/oasis-grow/setup_scripts

. /home/pi/oasis-grow/setup_scripts/setup_env.sh
. /home/pi/oasis-grow/setup_scripts/setup_config.sh
. /home/pi/oasis-grow/setup_scripts/setup_network.sh

#while getopts ":r:d:" opt; do
#    case $opt in
#        r)
#            echo "Adding rc.local bootloader..."
#            sudo chmod +x /home/pi/oasis-grow/setup_scripts/setup_rclocal.sh
#            . /home/pi/oasis-grow/setup_scripts/setup_rclocal.sh
#            
#            echo "Optimizing boot time..."
#            sudo chmod +x /home/pi/oasis-grow/setup_scripts/optimize_boot.sh
#            . /home/pi/oasis-grow/setup_scripts/optimize_boot.sh -b        
#            
#            ;;
#        systemd)
#            echo "Adding systemd service..."
#            sudo chmod +x /home/pi/oasis-grow/setup_scripts/setup_systemd.sh
#            . /home/pi/oasis-grow/setup_scripts/setup_systemd.sh
#            
#            echo "Optimizing boot time..."
#            sudo chmod +x /home/pi/oasis-grow/setup_scripts/optimize_boot.sh
#            . /home/pi/oasis-grow/setup_scripts/optimize_boot.sh -b        
#            
#            ;;
#        \?)
#            echo "Invalid option: -$OPTARG"
#            ;;
#    esac
#done

echo "Returning to WiFi mode..."
sudo cp /etc/dhcpcd_WiFi.conf /etc/dhcpcd.conf
sudo cp /etc/dnsmasq_WiFi.conf /etc/dnsmasq.conf
sudo systemctl disable hostapd
sudo systemctl reboot