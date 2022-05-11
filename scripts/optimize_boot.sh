#!/bin/sh -e

echo "Disabling non-essential services at boot"
sudo systemctl disable apt-daily.service
sudo systemctl disable apt-daily-upgrade.service
sudo systemctl disable man-db.service
echo "Removed apt-daily, apt-daily-upgrade, & man-db"
sudo systemctl disable dphys-swapfile.service
sudo systemctl disable avahi-daemon.service
sudo systemctl disable triggerhappy.service
echo "Removed dphys-swapfile, avahi-daemon, & triggerhappy"

#while getopts ":no_bt:no_wifi" opt; do
#    case $opt in
#        no_bt)
#            echo "Disabling bluetooth services at boot..."
#            sudo systemctl disable hciuart.service
#            sudo systemctl disable bluetooth.service
#            ;;
#        no_wifi)
#            echo "Disabling wifi services at boot..."
#            sudo systemctl disable wifi-country.service
#            sudo systemctl disable dhcpcd.service
#            sudo systemctl disable networking.service
#            sudo systemctl disable ssh.service
#            sudo systemctl disable ntp.service
#            sudo systemctl disable dnsmasq.service
#            sudo systemctl disable wpa_supplicant.service
#            ;;
#        \?)
#            echo "Invalid option: -$OPTARG"
#            ;;
#    esac
#done

echo "'Use systemd-analyze blame' & 'systemd-analyze critical-chain' to identify time-consuming processes on boot"
echo "Make edits to /boot/config.txt, /boot/cmdline.txt, and /etc/fstab to enable further optimizations"
echo "Editing configuration files carelessly may ruin your system. If making further edits, be warned!"
